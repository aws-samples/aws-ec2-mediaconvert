import boto3

import os
client = boto3.client("mediaconvert")


if __name__ == "__main__":
    response = client.describe_endpoints()

    print(response["Endpoints"][0]["Url"])
