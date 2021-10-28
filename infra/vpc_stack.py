from aws_cdk import (
    core as cdk,
    aws_ec2 as ec2,
)


class VPCStack(cdk.NestedStack):

    def __init__(self, scope: cdk.Construct, construct_id: str,
                 vpc_id: str = None, sg_id: str = None,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        if vpc_id is None:
            cidr = "10.30.0.0/16"

            self._vpc = ec2.Vpc(
                self,
                "VPC",
                max_azs=2,
                cidr=cidr,
                # Create 2 groups in 2 AZs
                subnet_configuration=[
                    ec2.SubnetConfiguration(
                        subnet_type=ec2.SubnetType.PUBLIC,
                        name="Public",
                        cidr_mask=24
                    ),
                    ec2.SubnetConfiguration(
                        subnet_type=ec2.SubnetType.PRIVATE,
                        name="Private",
                        cidr_mask=24
                    )
                ],
                nat_gateways=2,
            )
        else:
            self._vpc = ec2.Vpc.from_lookup(
                self,
                "VPC",
                vpc_id=vpc_id
            )

        if sg_id is None:
            self._security_group = ec2.SecurityGroup(
                self,
                "SecurityGroup",
                vpc=self._vpc,
                description="Security Group for Common",
            )

            self._security_group.add_ingress_rule(
                peer=ec2.Peer.any_ipv4(),
                connection=ec2.Port.tcp(22),
            )
        else:
            self._security_group = ec2.SecurityGroup.from_lookup(
                self,
                "SecurityGroup",
                security_group_id=sg_id
            )

        cdk.CfnOutput(
            self,
            "VPC ID",
            value=self._vpc.vpc_id
        )

        cdk.CfnOutput(
            self,
            "Security Group ID",
            value=self._security_group.security_group_id
        )

    @property
    def vpc(self):
        return self._vpc

    @property
    def sg(self):
        return self._security_group
