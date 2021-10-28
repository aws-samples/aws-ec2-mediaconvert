from aws_cdk import (
    core as cdk,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_sqs as sqs,
    aws_lambda as lambda_,
    aws_lambda_event_sources as eventsources,
)


class EventStack(cdk.NestedStack):

    def __init__(self, scope: cdk.Construct, construct_id: str,
                 vpc: ec2.Vpc, sg: ec2.SecurityGroup,
                 target_url: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # SQS, Source Bucket and Lambda
        source_queue = sqs.Queue(
            self,
            "SourceQueue",
        )

        self._src_bucket = s3.Bucket(
            self,
            "SourceBucket",
        )
        self._src_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.SqsDestination(source_queue),
            s3.NotificationKeyFilter(
                prefix="temp/",
            )
        )

        sqs_lambda_role = iam.Role(
            self,
            "SQSLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaSQSQueueExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
            ]
        )

        sqs_lambda = lambda_.Function(
            self,
            "DSSQSPoller",
            handler="lambda_handler.handler",
            runtime=lambda_.Runtime.PYTHON_3_8,
            code=lambda_.Code.from_asset('lambdas/sqs_poller'),
            timeout=cdk.Duration.seconds(25),
            role=sqs_lambda_role,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE
            ),
            security_groups=[sg],
            environment={
                "TARGET_URL": target_url
            }
        )

        sqs_lambda.add_event_source(eventsources.SqsEventSource(source_queue))

    @property
    def bucket_name(self):
        return self._src_bucket.bucket_name
