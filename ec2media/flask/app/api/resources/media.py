import boto3
import json
import os

from flask import Blueprint, request
from flask_restful import Api, Resource

media_bp = Blueprint('media', __name__)
media_api = Api(media_bp)

endpoint_url = os.environ["ENDPOINT"]
account = os.environ["ACCOUNT"]
region = os.environ["REGION"]
bucket = os.environ["BUCKET"]

mediaconvert_client = boto3.client(
    'mediaconvert',
    region_name=region,
    endpoint_url=endpoint_url
)


class MeidaResource(Resource):
    def post(self):
        json_data = request.json
        print(json_data)

        queue_arn = f"arn:aws:mediaconvert:{region}:{account}:queues/Default"
        role_arn = f"arn:aws:iam::{account}:role/MediaConvert_Default_Role"
        file_output = f"s3://{bucket}/output/"

        s3 = json_data["Records"][0]["s3"]
        object_key = s3["object"]["key"]
        file_input = f"s3://{bucket}/{object_key}"
        print(file_input)

        with open("resource/mp4.json", "r") as json_file:
            job_object = json.load(json_file)

        job_object["Queue"] = queue_arn
        job_object["Role"] = role_arn
        job_object["Settings"]["OutputGroups"][0]["OutputGroupSettings"]["FileGroupSettings"]["Destination"] = file_output
        job_object["Settings"]["Inputs"][0]["FileInput"] = file_input
        print(job_object)

        res = mediaconvert_client.create_job(**job_object)

        return {"job": res["Job"]["Id"]}


media_api.add_resource(MeidaResource, '/media')
