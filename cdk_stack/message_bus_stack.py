from aws_cdk import (
    Aws,
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_apigateway as apigw_,
    aws_dynamodb as dynamodb_,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_lambda_event_sources as lambda_events,
    aws_logs as logs,
    aws_sqs as sqs_,
)
from aws_cdk.aws_dynamodb import BillingMode
from constructs import Construct

MESSAGES_TABLE_NAME = "messages"


class MessageBusStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # IAM Roles
        # Create the API GW service role with permissions to call SQS
        # TODO: setup CORS
        rest_api_role = iam.Role(
            self,
            "RestAPIRole",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
            managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSQSFullAccess")]
            # TODO: less privileges
        )
        lambda_role = iam.Role(
            self,
            "LambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonDynamoDBFullAccess")]
            # TODO: less privileges
        )

        # SQS
        dlq = sqs_.Queue(
            self,
            id="DeadLetterQueue",
            retention_period=Duration.days(7)
        )
        dead_letter_queue = sqs_.DeadLetterQueue(
            max_receive_count=1,
            queue=dlq
        )
        message_queue = sqs_.Queue(
            self,
            "MessageQueue",
            visibility_timeout=Duration.seconds(30),
            receive_message_wait_time=Duration.seconds(20),
            dead_letter_queue=dead_letter_queue
        )

        # DynamoDB
        message_db_table = dynamodb_.Table(
            self,
            MESSAGES_TABLE_NAME,
            partition_key=dynamodb_.Attribute(name="id", type=dynamodb_.AttributeType.STRING),
            removal_policy=RemovalPolicy.DESTROY,
            billing_mode=BillingMode.PAY_PER_REQUEST
        )

        # Lambda
        consume_sqs_message_handler = lambda_.Function(
            self,
            "MessageConsumerHandler",
            function_name="consume_message_handler",
            runtime=lambda_.Runtime.PYTHON_3_12,
            code=lambda_.Code.from_asset("lambda/sqs_consumer"),
            handler="index.handler",
            memory_size=512,
            timeout=Duration.seconds(15),
            role=lambda_role
        )
        consume_sqs_message_handler.add_environment("MESSAGE_TABLE_NAME",
                                                    message_db_table.table_name)

        get_single_message_api_handler = lambda_.Function(
            self,
            "GetMessageHandler",
            function_name="get_message_handler",
            runtime=lambda_.Runtime.PYTHON_3_12,
            code=lambda_.Code.from_asset("lambda/api"),
            handler="index.handler",
            memory_size=512,
            timeout=Duration.seconds(15),
            role=lambda_role
        )
        get_single_message_api_handler.add_environment("MESSAGE_TABLE_NAME",
                                                       message_db_table.table_name)
        get_single_message_api_handler.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AWSLambdaBasicExecutionRole")
        )

        # API Gateway
        base_api = apigw_.RestApi(self, "ApiGateway", description="API Gateway")
        messages_resource = base_api.root.add_resource("messages")
        get_message_by_id_resource = messages_resource.add_resource("{id}")
        integration_response = apigw_.IntegrationResponse(
            status_code="200",
            response_templates={"application/json": ""},
        )
        api_integration_options = apigw_.IntegrationOptions(
            credentials_role=rest_api_role,
            integration_responses=[integration_response],
            request_templates={"application/json": "Action=SendMessage&MessageBody=$input.body"},
            passthrough_behavior=apigw_.PassthroughBehavior.NEVER,
            request_parameters={
                "integration.request.header.Content-Type": "'application/x-www-form-urlencoded'"},
        )
        send_message_integration = apigw_.AwsIntegration(
            service="sqs",
            integration_http_method="POST",
            options=api_integration_options,
            path="{}/{}".format(Aws.ACCOUNT_ID, message_queue.queue_name),
        )
        messages_resource.add_method(
            "POST",
            send_message_integration,
            method_responses=[apigw_.MethodResponse(status_code="200")]
        )

        single_message_integration = apigw_.LambdaIntegration(
            handler=get_single_message_api_handler,
        )
        get_message_by_id_resource.add_method(
            "GET",
            single_message_integration,
            method_responses=[apigw_.MethodResponse(status_code="200")]
        )

        # TODO: Add log group

        log_group = logs.LogGroup(
            self,
            "LambdaLogGroup",
            log_group_name=f"/aws/lambda/{get_single_message_api_handler.function_name}",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_DAY,
        )

        sqs_event_source = lambda_events.SqsEventSource(message_queue)
        consume_sqs_message_handler.add_event_source(sqs_event_source)

        message_db_table.grant_write_data(consume_sqs_message_handler)
        message_db_table.grant_read_data(get_single_message_api_handler)

        # SNS
        # TODO:

        # Define outputs
        CfnOutput(
            self,
            "ApiHostUrl",
            value=f"{base_api.rest_api_id}.execute-api.{Aws.REGION}.amazonaws.com",
            description="API Host URL"
        )
