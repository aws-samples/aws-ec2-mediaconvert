#!/usr/bin/env python3
import os

from aws_cdk import core as cdk

from infra.cicd_stack import CICDPipeline
from infra.vpc_stack import VPCStack
from infra.event_stack import EventStack
from infra.instance_stack import InstanceStack

account = os.environ["CDK_DEFAULT_ACCOUNT"]
region = os.environ["CDK_DEFAULT_REGION"]
endpoint_url = os.environ["ENDPOINT_URL"]

app = cdk.App()

ec2_media_stack = cdk.Stack(
    app,
    "EC2Media",
    env=cdk.Environment(account=account, region=region),
)

vpc_stack = VPCStack(
    ec2_media_stack,
    "VPC",
)

instance_stack = InstanceStack(
    ec2_media_stack,
    "Instance",
    vpc=vpc_stack.vpc,
    sg=vpc_stack.sg,
    region=region
)
instance_stack.add_dependency(vpc_stack)

event_stack = EventStack(
    ec2_media_stack,
    "Event",
    vpc=vpc_stack.vpc,
    sg=vpc_stack.sg,
    target_url=instance_stack.alb_dns_name,
)
event_stack.add_dependency(instance_stack)

cicd_stack = CICDPipeline(
    ec2_media_stack,
    "CICD",
    account=account,
    region=region,
    server_application_name=instance_stack.application_name,
    deployment_group_name=instance_stack.deployment_group_name,
    instance_profile_arn=instance_stack.instance_profile_arn,
    endpoint_url=endpoint_url,
    bucket_name=event_stack.bucket_name,
)
cicd_stack.add_dependency(event_stack)

app.synth()
