from typing import Callable, Iterable

import boto3
from botocore.exceptions import ClientError

from memegenerator import MemeTemplate, TextBox

class TemplateStore:
    def __init__(self, access_key, secret, region, default_templates: Callable[[],Iterable[MemeTemplate]]):
        self.dynamodb = boto3.client("dynamodb",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret,
            region_name = region)
        self.default_templates = default_templates

    def template_table(self, guild: str) -> 'boto3.resources.factory.dynamodb.Table':
        table_name = guild + "::templates"
        try:
            table = self.dynamodb.table(table_name)
            if table.table_status in ("CREATING", "UPDATING", "DELETING", "ACTIVE"):
                return table
        except ClientError:
            return self._init_table(table_name)       


    def _init_table(self, table_name: str) -> 'boto3.resources.factory.dynamodb.Table':
        table = self.dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'name',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'name',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

        #wait for the table to be created
        table.meta.client.get_waiter('table_exists').wait(TableName=table_name)     

        for t in self.default_templates():
            writeTemplate(t)
        return table


    def readTemplate(self, guild: str, id: str) -> MemeTemplate:
        table = self.template_table(guild)
        return MemeTemplate.deserialize(table.get_item(id))
    
    def writeTemplate(self, guild: str, template: MemeTemplate):
        table = self.template_table(guild)
        table.put_item(template.serialize(True))
