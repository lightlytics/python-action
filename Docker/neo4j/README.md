#Build neo4j docker image
1. docker build -t lightlytics/neo4j:latest .
2. docker tag lightlytics/neo4j:latest 219342927623.dkr.ecr.us-east-1.amazonaws.com/lightlytics/neo4j:latest
3. aws ecr get-login-password | docker login --username AWS --password-stdin 219342927623.dkr.ecr.us-east-1.amazonaws.com/lightlytics
4. docker push 219342927623.dkr.ecr.us-east-1.amazonaws.com/lightlytics/neo4j:latest

