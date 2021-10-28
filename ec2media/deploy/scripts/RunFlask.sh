#!/bin/bash
aws ecr get-login-password --region <REGION> | docker login --username AWS --password-stdin <ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com
sudo docker pull <ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/<ECR_NAME>:latest
sudo docker stop $(docker ps -a -q)
sudo docker rm $(docker ps -a -q)
sudo docker run --restart=always -d -p 80:80 -e ENDPOINT=<ENDPOINT> -e REGION=<REGION> -e BUCKET=<BUCKET> -e ACCOUNT=<ACCOUNT> <ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/<ECR_NAME>:latest
