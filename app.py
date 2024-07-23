#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk_stack.message_consumer import MessageConsumerStack

app = cdk.App()
MessageConsumerStack(app, "GpsPositionPublisherStack", )

app.synth()
