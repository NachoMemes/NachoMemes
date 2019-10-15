# pylint: skip-file
 
from decimal import Decimal
from typing import Callable, Iterable, List, Any, Type, Dict
from operator import attrgetter
from urllib.request import Request
from dacite import from_dict

import boto3
from botocore.exceptions import ClientError

from store import Store, TemplateError, MemeTemplate, Font, Color, Justify, da_config

dynamo_serializers = {
    Request: attrgetter("full_url"),
    float: lambda f: Decimal(str(f)),
    Font: attrgetter("name"),
    Color: attrgetter("name"),
    Justify: attrgetter("name"),
}

def update_serialization(value: Any, serializers: Dict[Type,Callable]):
    if type(value) in serializers:
        return serializers[type(value)](value)
    if dict == type(value):
        return { k: update_serialization(v, serializers) for k,v in value.items() }
    if list == type(value):
        return [ update_serialization(v, serializers) for v in value ]
    return value


class DynamoTemplateStore(Store):
    def __init__(self, access_key, secret, region, default_templates: Store, beta: bool=False):
        self.dynamodb = boto3.resource(
            "dynamodb",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret,
            region_name=region,
        )
        self.default_templates = default_templates
        self.table_suffix = ".templates" if not beta else ".templates-beta"

    def _template_table(
        self, guild: str, populate: bool = True
    ) -> "boto3.resources.factory.dynamodb.Table":
        table_name = guild + self.table_suffix
        try:
            table = self.dynamodb.Table(table_name)
            if table.table_status in ("CREATING", "UPDATING", "ACTIVE"):
                return table
            table.meta.client.get_waiter("table_not_exists").wait(TableName=table_name)
        except ClientError:
            pass
        print("creating table" + table_name)
        # create and return table
        table = self._init_table(table_name)
        if populate:
            self.refresh_memes(guild)
        return table

    def guild_config(self, guild: str) -> dict:
        pass

    def refresh_memes(self, guild: str, hard: bool = False) -> str:
        if hard:
            table_name = guild + self.table_suffix
            table = self.dynamodb.Table(table_name)
            if table.table_status in ("CREATING", "UPDATING", "ACTIVE"):
                table.delete()
            table.meta.client.get_waiter("table_not_exists").wait(TableName=table_name)

        table = self._template_table(guild, False)
        updated = 0
        added = 0
        unchanged = 0
        for item in self.default_templates.list_memes(guild):
            if "usage" in item:
                del item["usage"]
            name = item.pop("name")
            item = update_serialization(item, dynamo_serializers)
            prior = table.update_item(
                Key={"name": name},
                UpdateExpression=f"SET {','.join(f'#{k}=:{k}' for k in item)}",
                ExpressionAttributeValues={f":{k}": v for k, v in item.items()},
                ExpressionAttributeNames={f"#{k}": k for k in item},
                ReturnValues="UPDATED_OLD",
            ).get("Attributes", None)
            if not prior:
                added += 1
            elif item != prior:
                updated += 1
            else:
                unchanged += 1
        return f"{'hard ' if hard else ''}refresh on '{guild}.templates' complete: {added} added, {updated} updated, {unchanged} unchanged"

    def _init_table(self, table_name: str) -> "boto3.resources.factory.dynamodb.Table":
        table = self.dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{"AttributeName": "name", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "name", "AttributeType": "S"}],
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )

        # wait for the table to be created
        table.meta.client.get_waiter("table_exists").wait(TableName=table_name)
        return table

    def _fetch(self, table: "boto3.resources.factory.dynamodb.Table", key: dict) -> dict: 
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
                ExpressionAttributeNames={"#usage": "usage", "#source_image_url": "source_image_url"},
                ExpressionAttributeValues={":one": Decimal(1), ":zero": Decimal(0)},
                ReturnValues="ALL_NEW",
            )["Attributes"]
        except ClientError:
            raise TemplateError

    def list_memes(self, guild: str, fields: List[str] = None) -> Iterable[dict]:
        table = self._template_table(guild)
        if not fields:
            return table.scan()["Items"]
        else:
            return table.scan(
                ProjectionExpression=",".join(f"#{k}" for k in fields),
                ExpressionAttributeNames={f"#{k}": k for k in fields},
            )["Items"]

    def read_meme(
        self, guild: str, id: str, increment_use: bool = False
    ) -> MemeTemplate:
        table, key = self._template_table(guild), {"name": id}
        item = (self._increment_usage_and_fetch if increment_use else self._fetch)(
            table, key
        )
        return from_dict(MemeTemplate, item, config=da_config)

  