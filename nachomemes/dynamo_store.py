from decimal import Decimal
from operator import attrgetter
from typing import Any, Callable, Dict, Iterable, List, Type, Union, Sequence, Optional
from urllib.request import Request
from enum import Enum, auto
from dataclasses import asdict


import boto3
from botocore.exceptions import ClientError
from dacite import from_dict
from discord import Guild

from .guild_config import GuildConfig
from .store import Color, Font, Justify, MemeTemplate, Store, TemplateError, da_config, guild_id, update_serialization



class Result(Enum):
    ADDED = auto()
    UPDATED = auto()
    UNCHANGED = auto()






class DynamoTemplateStore(Store):
    def __init__(
        self, access_key, secret, region, default_store: Store, beta: bool = False
    ):
        self.dynamodb = boto3.resource(
            "dynamodb",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret,
            region_name=region,
        )
        self.default_store = default_store
        self.table_suffix = ".templates" if not beta else ".templates-beta"
        self.config_suffix = ".config" if not beta else ".config-beta"

    def _template_table(self, guild: Optional[Guild], populate: bool = True) -> "boto3.resources.factory.dynamodb.Table":
        table_name = guild_id(guild) + self.table_suffix
        try:
            table = self.dynamodb.Table(table_name)
            if table.table_status in ("CREATING", "UPDATING", "ACTIVE"):
                return table
            table.meta.client.get_waiter("table_not_exists").wait(TableName=table_name)
        except ClientError:
            pass
        print("creating table" + table_name)
        # create and return table
        table = self._init_table(table_name, ("name",))
        if populate:
            self.refresh_memes(guild)
        return table

    def _config_table(self, guild: Union[Guild,GuildConfig,None], populate: bool = True) -> "boto3.resources.factory.dynamodb.Table":
        table_name = guild_id(guild) + self.config_suffix
        try:
            table = self.dynamodb.Table(table_name)
            if table.table_status in ("CREATING", "UPDATING", "ACTIVE"):
                return table
            table.meta.client.get_waiter("table_not_exists").wait(TableName=table_name)
        except ClientError:
            pass
        print("creating table" + table_name)
        # create and return table
        table = self._init_table(table_name, ("id",))
        if populate:
            self.save_guild_config(self.default_store.guild_config(guild))
        return table


    def guild_config(self, guild: Guild) -> GuildConfig:
        table = self._config_table(guild)
        item = self._fetch(table, {"id": guild_id(guild)})
        return from_dict(GuildConfig, item, config=da_config)

    def save_guild_config(self, guild: GuildConfig):
        table = self._config_table(guild, False)
        self._write(table, ("id",), asdict(guild))


    def _write(self, table: "boto3.resources.factory.dynamodb.Table", keys: Iterable[str], value: Dict[str,Any]):
        item = update_serialization(value)
        key = {k:item.pop(k) for k in keys}
        prior = table.update_item(
            Key=key,
            UpdateExpression=f"SET {','.join(f'#{k}=:{k}' for k in item)}",
            ExpressionAttributeValues={f":{k}": v for k, v in item.items()},
            ExpressionAttributeNames={f"#{k}": k for k in item},
            ReturnValues="UPDATED_OLD",
        ).get("Attributes", None)
        if not prior:
            return Result.ADDED
        elif item != prior:
            return Result.UPDATED
        else:
            return Result.UNCHANGED

    def _delete_table(self, name: str):
        try:
            table = self.dynamodb.Table(name)
            if table.table_status in ("CREATING", "UPDATING", "ACTIVE"):
                print("deleting: " + name)
                table.delete()
            table.meta.client.get_waiter("table_not_exists").wait(TableName=name)
        except ClientError:
            pass


    def refresh_memes(self, guild: Optional[Guild], hard: bool = False) -> str:
        if hard:
            self._delete_table(guild_id(guild) + self.config_suffix)
            self._delete_table(guild_id(guild) + self.table_suffix)

        table = self._template_table(guild, False)
        results = {Result.ADDED: 0, Result.UPDATED: 0, Result.UNCHANGED: 0}
        for item in self.default_store.list_memes(guild):
            if "usage" in item:
                del item["usage"]
            r = self._write(table, ("name",), item)
            results[r] += 1
        return f"{'hard ' if hard else ''}refresh on '{guild_id(guild)}.templates' complete: {results[Result.ADDED]} added, {results[Result.UPDATED]} updated, {results[Result.UNCHANGED]} unchanged"

    def _init_table(self, table_name: str, keys=Sequence[str]) -> "boto3.resources.factory.dynamodb.Table":
        table = self.dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{"AttributeName": k, "KeyType": "HASH"} for k in keys],
            AttributeDefinitions=[{"AttributeName": k, "AttributeType": "S"} for k in keys],
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )

        # wait for the table to be created
        table.meta.client.get_waiter("table_exists").wait(TableName=table_name)
        return table

    def _fetch(
        self, table: "boto3.resources.factory.dynamodb.Table", key: dict
    ) -> dict:
        try:
            return table.get_item(Key=key)["Item"]
        except KeyError:
            raise TemplateError

    def _increment_usage_and_fetch(
        self, table: "boto3.resources.factory.dynamodb.Table", key: dict
    ):
        try:
            return table.update_item(
                Key=key,
                ConditionExpression="attribute_exists(#source_image_url)",
                UpdateExpression="set #usage = if_not_exists(#usage, :zero) + :one",
                ExpressionAttributeNames={
                    "#usage": "usage",
                    "#source_image_url": "source_image_url",
                },
                ExpressionAttributeValues={":one": Decimal(1), ":zero": Decimal(0)},
                ReturnValues="ALL_NEW",
            )["Attributes"]
        except ClientError:
            raise TemplateError

    def list_memes(self, guild: Union[Guild, str, None]=None, fields: List[str] = None) -> Iterable[dict]:
        table = self._template_table(guild)
        if not fields:
            return table.scan()["Items"]
        else:
            return table.scan(
                ProjectionExpression=",".join(f"#{k}" for k in fields),
                ExpressionAttributeNames={f"#{k}": k for k in fields},
            )["Items"]

    def get_meme(
        self, guild: Optional[Guild], id: str, increment_use: bool = False
    ) -> dict:
        table, key = self._template_table(guild), {"name": id}
        return (self._increment_usage_and_fetch if increment_use else self._fetch)(
            table, key
        )

    def save_meme(self, guild: Optional[Guild], item: dict) -> str:
        table = self._template_table(guild, False)
        r = self._write(table, ("name",), item)
        return f"meme {r}"