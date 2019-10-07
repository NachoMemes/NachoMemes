from typing import Callable, Iterable
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError

from memegenerator import MemeTemplate, TextBox

class TemplateError(Exception):
    pass

class TemplateStore:
    def __init__(
        self,
        access_key,
        secret,
        region,
        default_templates: Callable[[str], Iterable[MemeTemplate]],
    ):
        self.dynamodb = boto3.resource(
            "dynamodb",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret,
            region_name=region,
        )
        self.default_templates = default_templates

    def _template_table(self, guild: str) -> "boto3.resources.factory.dynamodb.Table":
        table_name = guild + ".templates"
        try:
            table = self.dynamodb.Table(table_name)
            if table.table_status in ("CREATING", "UPDATING", "DELETING", "ACTIVE"):
                return table
        except ClientError:
            print("creating table" + table_name)
        # create and return table
        table = self._init_table(table_name)
        self.refresh(guild)
        return table

    def refresh(self, guild: str):
        table = self._template_table(guild)
        for t in self.default_templates(guild):
            table.put_item(Item=t.serialize(True))

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

    def _fetch(self, table: "boto3.resources.factory.dynamodb.Table", key: dict):
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
                UpdateExpression="set #attr = #attr + :val",
                ExpressionAttributeNames={"#attr": "usage"},
                ExpressionAttributeValues={":val": Decimal(1)},
                ReturnValues="ALL_NEW",
            )["Attributes"]
        except ClientError:
            raise TemplateError

    def list_memes(self, guild: str) -> Iterable[dict]:
        table = self._template_table(guild)
        return table.scan(
            ProjectionExpression="#attr1, #attr2",
            ExpressionAttributeNames={"#attr1": "name", "#attr2": "description"},
        )["Items"]

    def read_meme(
        self, guild: str, id: str, increment_use: bool = False
    ) -> MemeTemplate:
        table, key = self._template_table(guild), {"name": id}
        item =  (self._increment_usage_and_fetch if increment_use else self._fetch)(table, key)
        return MemeTemplate.deserialize(item)

    def _write_meme(self, guild: str, template: MemeTemplate):
        table = self._template_table(guild)
        table.put_item(template.serialize(True))
