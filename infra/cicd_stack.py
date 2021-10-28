from aws_cdk import (
    core as cdk,
    aws_codebuild as codebuild,
    aws_codecommit as codecommit,
    aws_codepipeline as codepipeline,
    aws_codedeploy as codedeploy,
    aws_codepipeline_actions as codepipeline_actions,
    aws_iam as iam,
    aws_ecr as ecr,
    aws_s3 as s3,
)


class CICDPipeline(cdk.NestedStack):

    def __init__(self, scope: cdk.Construct, construct_id: str,
                 account: str, region: str, endpoint_url: str, bucket_name: str, instance_profile_arn: str,
                 server_application_name: str, deployment_group_name: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ECR
        repo = ecr.Repository(
            self,
            "RepoFlask",
            repository_name="ec2media-app"
        )

        # CodeCommit
        code = codecommit.Repository(
            self,
            "SourceRepo",
            repository_name="ec2media"
        )

        # CodePipeline
        pipeline = codepipeline.Pipeline(
            self,
            "Pipeline",
        )

        ec2_instance_profile_role = iam.Role.from_role_arn(
            self,
            "EC2MediaInstanceRole",
            role_arn=instance_profile_arn
        )

        pipeline.artifact_bucket.grant_read(ec2_instance_profile_role)

        # Source Stage
        source_code = codepipeline.Artifact()
        pipeline.add_stage(
            stage_name="Source",
            actions=[
                codepipeline_actions.CodeCommitSourceAction(
                    action_name="Source",
                    branch="master",
                    repository=code,
                    output=source_code,
                )
            ]
        )

        # Build Stage
        build_spec_obj = {
            "version": "0.2",
            "phases": {
                "pre_build": {
                    "commands": [
                        "echo Logging in to Amazon ECR...",
                        "aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT.dkr.ecr.$REGION.amazonaws.com"
                    ]
                },
                "build": {
                    "commands": [
                        "echo Build started on `date`",
                        "echo Building the Docker image...",
                        "docker build -t $ECR_NAME .",
                        "docker tag $ECR_NAME:latest $ACCOUNT.dkr.ecr.$REGION.amazonaws.com/$ECR_NAME:latest",
                        "echo Build completed on `date`",
                        "echo Pushing the Docker image...",
                        "docker push $ACCOUNT.dkr.ecr.$REGION.amazonaws.com/$ECR_NAME:latest"
                    ]
                },
                "post_build": {
                    "commands": [
                        'sed -i "s=<ACCOUNT>=$ACCOUNT=g" deploy/scripts/RunFlask.sh',
                        'sed -i "s=<REGION>=$REGION=g" deploy/scripts/RunFlask.sh',
                        'sed -i "s=<ECR_NAME>=$ECR_NAME=g" deploy/scripts/RunFlask.sh',
                        'sed -i "s=<ENDPOINT>=$ENDPOINT=g" deploy/scripts/RunFlask.sh',
                        'sed -i "s=<BUCKET>=$BUCKET=g" deploy/scripts/RunFlask.sh',
                    ]
                }
            },
            "artifacts": {
                "base-directory": "deploy",
                "files": ["**/*"]
            },
        }

        build_project = codebuild.PipelineProject(
            self,
            "ContainerBuild",
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
                privileged=True
            ),
            environment_variables={
                "REGION": codebuild.BuildEnvironmentVariable(value=region),
                "ACCOUNT": codebuild.BuildEnvironmentVariable(value=account),
                "ECR_NAME": codebuild.BuildEnvironmentVariable(value=repo.repository_name),
                "ENDPOINT": codebuild.BuildEnvironmentVariable(value=endpoint_url),
                "BUCKET": codebuild.BuildEnvironmentVariable(value=bucket_name),
            },
            build_spec=codebuild.BuildSpec.from_object(build_spec_obj),
        )
        build_project.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ecr:*"
                ],
                resources=["*"]
            )
        )

        deploy_code = codepipeline.Artifact()

        pipeline.add_stage(
            stage_name="Build",
            actions=[
                codepipeline_actions.CodeBuildAction(
                    action_name="Build",
                    project=build_project,
                    input=source_code,
                    outputs=[deploy_code],
                )
            ]
        )

        # Deploy Stage
        app = codedeploy.ServerApplication.from_server_application_name(
            self,
            "ServerApplication",
            server_application_name=server_application_name
        )
        dg = codedeploy.ServerDeploymentGroup.from_server_deployment_group_attributes(
            self,
            "ServerDeploymentGroup",
            application=app,
            deployment_group_name=deployment_group_name,
        )
        pipeline.add_stage(
            stage_name="Deploy",
            actions=[
                codepipeline_actions.CodeDeployServerDeployAction(
                    action_name="Deploy",
                    deployment_group=dg,
                    input=deploy_code,
                )
            ]
        )


