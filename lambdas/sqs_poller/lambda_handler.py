import os
import json
import urllib.request
import urllib.error


target_url = os.environ["TARGET_URL"]
url = f"http://{target_url}/api/media"


def handler(event, context):
    cnt = 0
    for record in event["Records"]:
        item = json.loads(record["body"])
        print(item)
        if "Records" in item:
            s3 = item["Records"][0]["s3"]
            object_size = s3["object"]["size"]
            if object_size > 0:
                item_bytes = json.dumps(item).encode("utf-8")

                try:
                    req = urllib.request.Request(url)
                    req.add_header("Content-Type", "application/json")
                    req.add_header("Content-Length", str(len(item_bytes)))
                    response = urllib.request.urlopen(req, item_bytes)
                    body = response.read().decode("utf-8")
                except urllib.error.HTTPError as e:
                    body = e.read().decode("utf-8")

                print(json.loads(body))
                cnt += 1

    return f"Successfully processed {cnt} messages."
