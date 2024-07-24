#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk_stack.message_bus_stack import MessageBusStack

app = cdk.App()
MessageBusStack(app, "MessageBusStack", )

app.synth()
