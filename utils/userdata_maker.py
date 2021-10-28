from aws_cdk import aws_ec2 as ec2


class UserdataMaker(object):
    """
    sudo yum update -y
    sudo yum install -y ruby
    sudo yum install -y wget
    wget https://aws-codedeploy-ap-northeast-2.s3.ap-northeast-2.amazonaws.com/latest/install
    chmod +x ./install
    sudo ./install auto
    sudo systemctl status codedeploy-agent
    """
    def __init__(self, region: str):
        self._data = ec2.UserData.for_linux()
        self._data.add_commands("sudo yum update -y")
        self._data.add_commands("sudo yum install -y ruby")
        self._data.add_commands("sudo yum install -y wget")
        self._data.add_commands(f"wget https://aws-codedeploy-{region}.s3.{region}.amazonaws.com/latest/install")
        self._data.add_commands("chmod +x ./install")
        self._data.add_commands("sudo ./install auto")
        self._data.add_commands("sudo systemctl status codedeploy-agent")

    @property
    def data(self):
        return self._data
