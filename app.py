#!/usr/bin/env python3
import os

import aws_cdk as cdk

from gps_position_publisher.gps_position_publisher_stack import GpsPositionPublisherStack

app = cdk.App()
GpsPositionPublisherStack(app, "GpsPositionPublisherStack",)

app.synth()
