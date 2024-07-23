import aws_cdk as core
import aws_cdk.assertions as assertions

from gps_position_publisher.gps_position_publisher_stack import GpsPositionPublisherStack

# example tests. To run these tests, uncomment this file along with the example
# resource in gps_position_publisher/gps_position_publisher_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = GpsPositionPublisherStack(app, "gps-position-publisher")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
