import logging

import boto3
import json
import os

logger = logging.getLogger()


def handler(event, context) -> dict:
    logger.info("EVENT: " + json.dumps(event))

    try:
        message_table_name = os.environ["MESSAGE_TABLE_NAME"]

        message_id = event["pathParameters"]["id"]
        if not message_id:
            return {
                "statusCode": 404,
                "headers": {"Content-Type": "application/json"},
                "body": {
                    "data": {
                        "status": "fail",
                        "message": f"No message found with id = '{message_id}'"
                    }
                }
            }

        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(message_table_name)

        response = table.get_item(Key={"id": message_id})
        item = response.get("Item", None)
        if item is None:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": {
                    "data": {
                        "status": "fail",
                        "message": f"No message found with id = '{message_id}'"
                    }
                }
            }

        return {
            "statusCode": 200,
            "body": json.dumps(item)
        }
    except Exception as ex:
        logger.warning(str(ex))
        return {
            "statusCode": 500,
            "body": str(ex)
        }
