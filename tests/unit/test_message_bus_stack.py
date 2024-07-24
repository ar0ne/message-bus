import aws_cdk as core
import aws_cdk.assertions as assertions

from cdk_stack.message_bus_stack import MessageBusStack


# def test_sqs_queue_created():
#     app = core.App()
#     stack = MessageBusStack(app, "message-bus")
#     template = assertions.Template.from_stack(stack)
#
# #     template.has_resource_properties("AWS::SQS::Queue", {
# #         "VisibilityTimeout": 300
# #     })
