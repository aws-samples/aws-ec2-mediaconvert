from aws_cdk import (
    core as cdk,
    aws_autoscaling as autoscaling,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
    aws_iam as iam,
    aws_codedeploy as codedeploy,
)

from utils.userdata_maker import UserdataMaker


class InstanceStack(cdk.NestedStack):
    def __init__(self, scope: cdk.Construct, construct_id: str,
                 vpc: ec2.Vpc, sg: ec2.SecurityGroup, region: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # MediaConvert_Default_Role
        # Regardless of how you create the IAM service role for MediaConvert to use,
        # if you use the name MediaConvert_Default_Role,
        # then the MediaConvert console uses it by default when you create jobs in the future.
        iam.Role(
            self,
            "MediaConvertDefaultRole",
            role_name="MediaConvert_Default_Role",
            assumed_by=iam.ServicePrincipal("mediaconvert.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonAPIGatewayInvokeFullAccess"),
            ]
        )

        # EC2
        amzn_linux = ec2.MachineImage.latest_amazon_linux(
            generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
            edition=ec2.AmazonLinuxEdition.STANDARD,
            virtualization=ec2.AmazonLinuxVirt.HVM,
            storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE,
            cpu_type=ec2.AmazonLinuxCpuType.X86_64
        )

        self._instance_role = iam.Role(
            self,
            "InstanceRole",
            role_name="EC2MediaInstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMPatchAssociation"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryReadOnly"),
                iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchLogsFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSElementalMediaConvertFullAccess"),
            ]
        )

        # ASG
        asg = autoscaling.AutoScalingGroup(
            self,
            "ASG",
            instance_type=ec2.InstanceType.of(
                instance_class=ec2.InstanceClass.BURSTABLE3,
                instance_size=ec2.InstanceSize.XLARGE
            ),
            machine_image=amzn_linux,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE
            ),
            security_group=sg,
            min_capacity=1,
            max_capacity=10,
            role=self._instance_role
        )

        # LaunchTemplate
        block_device = ec2.BlockDevice(
            device_name="/dev/xvda",
            volume=ec2.BlockDeviceVolume.ebs(
                volume_size=30,
                volume_type=ec2.EbsDeviceVolumeType.GP3,
                delete_on_termination=True,
            )
        )

        user_data = UserdataMaker(region=region)

        launch_template = ec2.LaunchTemplate(
            self,
            "LaunchTemplate",
            block_devices=[block_device],
            cpu_credits=ec2.CpuCredits.STANDARD,
            ebs_optimized=True,
            instance_type=ec2.InstanceType.of(
                instance_class=ec2.InstanceClass.BURSTABLE3,
                instance_size=ec2.InstanceSize.XLARGE
            ),
            machine_image=amzn_linux,
            role=self._instance_role,
            security_group=sg,
            user_data=user_data.data,
        )

        cfn_asg: autoscaling.CfnAutoScalingGroup = asg.node.default_child
        asg.node.try_remove_child("LaunchConfig")
        cfn_asg.launch_configuration_name = None
        cfn_lt: ec2.CfnLaunchTemplate = launch_template.node.default_child
        cfn_asg.launch_template = autoscaling.CfnAutoScalingGroup.LaunchTemplateSpecificationProperty(
            version=cfn_lt.attr_default_version_number,
            launch_template_id=cfn_lt.ref,
        )

        # ALB
        self._alb = elbv2.ApplicationLoadBalancer(
            self,
            "ALB",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE
            ),
            security_group=sg,
            internet_facing=False,
        )

        http_listener = self._alb.add_listener(
            "ALBHTTPListener",
            protocol=elbv2.ApplicationProtocol.HTTP,
            port=80,
        )

        target_group = http_listener.add_targets(
            "TargetGroup",
            target_group_name="tg-alb-1",
            protocol=elbv2.ApplicationProtocol.HTTP,
            port=80,
            targets=[asg],
            health_check=elbv2.HealthCheck(
                enabled=True,
                path="/health/"
            )
        )

        asg.scale_on_cpu_utilization(
            "CPUUtilization",
            target_utilization_percent=50
        )

        # CodeDeploy
        self._application = codedeploy.ServerApplication(
            self,
            "CodeDeployApplication",
            application_name="EC2MediaApp"
        )

        codedeploy_role = iam.Role(
            self,
            "CodeDeployServiceRole",
            assumed_by=iam.ServicePrincipal("codedeploy.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSCodeDeployRole"),
            ]
        )

        self._deployment_group = codedeploy.ServerDeploymentGroup(
            self,
            "CodeDeployDeploymentGroup",
            application=self._application,
            deployment_config=codedeploy.ServerDeploymentConfig.ONE_AT_A_TIME,
            auto_scaling_groups=[asg],
            load_balancer=codedeploy.LoadBalancer.application(target_group),
            install_agent=True,
            ignore_poll_alarms_failure=False,
            auto_rollback=codedeploy.AutoRollbackConfig(
                deployment_in_alarm=False,
                failed_deployment=True,
                stopped_deployment=True
            ),
            role=codedeploy_role,
        )

        cdk.CfnOutput(
            self,
            "ALB DNS Name",
            value=self._alb.load_balancer_dns_name
        )

        cdk.CfnOutput(
            self,
            "ALB Name",
            value=self._alb.load_balancer_name
        )

        cdk.CfnOutput(
            self,
            "ALB Full Name",
            value=self._alb.load_balancer_full_name
        )

    @property
    def alb_dns_name(self):
        return self._alb.load_balancer_dns_name

    @property
    def application_name(self):
        return self._application.application_name

    @property
    def deployment_group_name(self):
        return self._deployment_group.deployment_group_name

    @property
    def instance_profile_arn(self):
        return self._instance_role.role_arn
