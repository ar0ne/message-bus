import logging

import boto3
import json
import os

logger = logging.getLogger()


def handler(event, context) -> dict:
    try:
        message_table_name = os.environ["MESSAGE_TABLE_NAME"]

        sqs_message = event["Records"][0]["body"]
        message = json.loads(sqs_message)
        logging.debug(message)

        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(message_table_name)
        response = table.put_item(Item={
            "id": message["id"],
            "message": message["message"]
        })
        if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
            logging.debug("Message inserted successfully")
        else:
            logging.debug("Message request insertion failed")

        # TODO: send message to SNS topic

        sqs = boto3.client("sqs")
        sqs.delete_message(QueueUrl=event["Records"][0]["queueUrl"], ReceiptHandle=sqs_message)

        return {
            "statusCode": 200,
            "body": json.dumps({"status": "success", "message": "Notification sent"})
        }
    except Exception as ex:
        logging.info(str(ex))
        return {
            "statusCode": 500,
            "body": json.dumps({"status": "fail", "message": "Notification failed"})
        }
