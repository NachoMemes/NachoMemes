from dataclasses import asdict
from decimal import Decimal
from enum import Enum, auto
from typing import Any, Dict, Iterable, Optional, Sequence, Union

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from dacite import from_dict
from discord import Guild

from nachomemes.guild_config import GuildConfig
from nachomemes.store import Store, da_config, get_guild_id, update_serialization
from nachomemes.template import TemplateError

# DynamoDB operation results
class Result(Enum):
    ADDED = auto()
    UPDATED = auto()
    UNCHANGED = auto()


class DynamoTemplateStore(Store):
    """
    Read/write DynamoDB data store.
    A default store is used to read initial guild configuration and read templates to refresh them as memes.
    """
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

        # Use different tables for the beta bot
        self.table_suffix = ".templates" if not beta else ".templates-beta"
        self.config_suffix = ".config" if not beta else ".config-beta"

    def _template_table(self, guild_id: str, populate: bool = True) -> "boto3.resources.factory.dynamodb.Table":
        """
        Either gets the existing table for templates if it exists, or creates a new one.
        Can populate the table with memes from the default store if specified by the argument.
        """
        table_name = guild_id + self.table_suffix
        try:
            table = self.dynamodb.Table(table_name)
            if table.table_status in ("CREATING", "UPDATING", "ACTIVE"):
                return table
            # Wait until the table doesn't exist (it is done being deleted, or if it doesn't exist yet)
            table.meta.client.get_waiter("table_not_exists").wait(TableName=table_name)
        except ClientError:
            pass
        print("creating table" + table_name)
        # create and return table
        table = self._init_table(table_name, ("name",))
        if populate:
            self.refresh_memes(guild_id)
        return table

    def _config_table(self, guild: Union[Guild,GuildConfig,None], populate: bool = True) -> "boto3.resources.factory.dynamodb.Table":
        """
        Either gets the existing table for guild configuration if it exists, or creates a new one.
        Can populate the table with the guild configuration from the default store if specified by the argument.
        """
        table_name = get_guild_id(guild) + self.config_suffix
        try:
            table = self.dynamodb.Table(table_name)
            if table.table_status in ("CREATING", "UPDATING", "ACTIVE"):
                return table
            # Wait until the table doesn't exist (it is done being deleted, or if it doesn't exist yet)
            table.meta.client.get_waiter("table_not_exists").wait(TableName=table_name)
        except ClientError:
            pass
        print("creating table" + table_name)
        # create and return table
        table = self._init_table(table_name, ("guild_id",))
        if populate:
            if isinstance(guild, GuildConfig):
                self.save_guild_config(guild)
            else:
                self.save_guild_config(self.default_store.guild_config(guild))
        return table


    def guild_config(self, guild: Optional[Guild]) -> GuildConfig:
        table = self._config_table(guild)
        try:
            item = self._fetch(table, {"guild_id": get_guild_id(guild)})
        except ClientError:
            # maybe using old key? 
            item = self._fetch(table, {"id": get_guild_id(guild)})
            item['guild_id'] = item.pop('id')
            print("old config, need refresh")
        return from_dict(GuildConfig, item, config=da_config)

    def save_guild_config(self, guild: GuildConfig) -> None:
        table = self._config_table(guild, False)
        self._write(table, ("guild_id",), asdict(guild))

    def _write(self, table: "boto3.resources.factory.dynamodb.Table", keys: Iterable[str], value: Dict[str, Any]) -> Result:
        item = update_serialization(value)
        key = {k: item.pop(k) for k in keys}
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

    def _delete_table(self, name: str) -> None:
        try:
            table = self.dynamodb.Table(name)
            if table.table_status in ("CREATING", "UPDATING", "ACTIVE"):
                print("deleting: " + name)
                table.delete()
            # Wait for the table to be deleted
            table.meta.client.get_waiter("table_not_exists").wait(TableName=name)
        except ClientError:
            pass

    def refresh_memes(self, guild_id: str, hard: bool = False) -> str:
        # Drop the templates table and the guild configuration table if a hard reset is requested
        if hard:
            self._delete_table(guild_id + self.config_suffix)
            self._delete_table(guild_id + self.table_suffix)

        table = self._template_table(guild_id, False)
        results = {Result.ADDED: 0, Result.UPDATED: 0, Result.UNCHANGED: 0}
        for item in self.default_store.list_memes(guild_id):
            # Don't change the usage values as we want to keep them between refreshes
            if "usage" in item:
                del item["usage"]
            r = self._write(table, ("name",), item)
            results[r] += 1
        return f"{'hard ' if hard else ''}refresh on '{guild_id}.templates' complete: {results[Result.ADDED]} added, {results[Result.UPDATED]} updated, {results[Result.UNCHANGED]} unchanged"

    def _init_table(self, table_name: str, keys=Sequence[str]) -> "boto3.resources.factory.dynamodb.Table":
        table = self.dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{"AttributeName": k, "KeyType": "HASH"} for k in keys],
            AttributeDefinitions=[
                {"AttributeName": k, "AttributeType": "S"} for k in keys],
            ProvisionedThroughput={
                "ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )

        # wait for the table to be created
        table.meta.client.get_waiter("table_exists").wait(TableName=table_name)
        return table

    def _fetch(
        self, table: "boto3.resources.factory.dynamodb.Table", key: dict
    ) -> dict:
        try:
            return table.get_item(Key=key).get("Item")
        except KeyError as err:
            raise TemplateError from err

    def _increment_usage_and_fetch(
        self, table: "boto3.resources.factory.dynamodb.Table", key: dict
    ) -> dict:
        try:
            return table.update_item(
                Key=key,
                ConditionExpression="attribute_exists(#image_url)",
                UpdateExpression="set #usage = if_not_exists(#usage, :zero) + :one",
                ExpressionAttributeNames={
                    "#usage": "usage",
                    "#image_url": "image_url",
                },
                ExpressionAttributeValues={
                    ":one": Decimal(1), ":zero": Decimal(0)},
                ReturnValues="ALL_NEW",
            )["Attributes"]
        except ClientError as err:
            raise TemplateError from err

    def list_memes(self, guild_id: str, is_deleted: Optional[bool] = False, fields: Optional[Iterable[str]] = None) -> Iterable[dict]:
        table = self._template_table(guild_id)

        query_parameters = {}

        if fields:
            query_parameters['ProjectionExpression'] = ",".join(f"#{k}" for k in fields)
            query_parameters['ExpressionAttributeNames'] = {f"#{k}": k for k in fields}

        if not is_deleted:
            query_parameters['FilterExpression'] = Attr('name').ne('successkid')
        
        return table.scan(**query_parameters)["Items"]

    def get_template_data(
        self, guild_id: str, template_id: str, increment_use: bool = False
    ) -> dict:
        table, key = self._template_table(guild_id), {"name": template_id}
        return (self._increment_usage_and_fetch if increment_use else self._fetch)(
            table, key
        )

    def save_meme(self, guild_id: str, item: dict) -> str:
        table = self._template_table(guild_id, False)
        r = self._write(table, ("name",), item)
        return f"meme {r}"
