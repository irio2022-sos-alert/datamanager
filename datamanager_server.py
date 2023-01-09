import asyncio
import logging

import grpc
import datamanager_pb2
import datamanager_pb2_grpc

from google.protobuf import empty_pb2
from google.cloud import scheduler_v1
from google.cloud import pubsub_v1

from dotenv import load_dotenv
import os
import json


config = {}
client = scheduler_v1.CloudSchedulerClient()
publisher = pubsub_v1.PublisherClient()

# Inherit from example_pb2_grpc.ExampleServiceServicer
# ExampleServiceServicer is the server-side artifact.
class DataManagerServicer(datamanager_pb2_grpc.DataManagerServicer): 
    async def ChangeConfig(self, request, context):

        # TODO(developer): Uncomment and set the following variables
        project_id = os.environ.get('PROJECT_ID')
        topic_id = os.environ.get('TOPIC_ID')

        name = request.name
        job_name = config[name]["job_name"]

        dic = {
            "name": request.name,
            "url": request.url,
            "frequency": request.frequency,
            "alerting_window": request.alerting_window,
            "allowed_resp_time": request.allowed_resp_time,
            "phone_number": request.phone_number,
            "email": request.email,
            "job_name": job_name
        }

        config[name] = dic

        job = {
            "schedule": f"*/{request.frequency} * * * *",

            "pub_sub_target": {
                "topic_name": f"projects/{project_id}/topics/{topic_id}",
                "data": "ping task",
                "attributes": {
                    "name": dic["name"],
                    "url": dic["url"],
                }
            }
        }

        # Make the request
        response = client.update_job(request={"name": job_name, "job": job})

        # Handle the response
        print(response)

        return empty_pb2.Empty()

def parse_config() -> dict:
    dic = {}
    data = ""
    with open("config.json") as config_file:
        data = json.load(config_file)

    for service in data:
        dic[service["name"]] = service

    return dic

async def serve() -> None:
    server = grpc.aio.server()
    datamanager_pb2_grpc.add_DataManagerServicer_to_server(
        DataManagerServicer(), server
    )

    server.add_insecure_port("[::]:50051")
    await server.start()
    await server.wait_for_termination()

def set_tasks() -> None:

    for task_config in config:
        project_id = os.environ.get('PROJECT_ID')
        location_id = os.environ.get('LOCATION_ID')
        topic_id = os.environ.get('TOPIC_ID')

        # Construct the fully qualified location path.
        parent = f"projects/{project_id}/locations/{location_id}"
        
        freq = task_config["frequency"]

        job = {
            "schedule": f"*/{freq} * * * *",
            "timeZone": "cet",

            "pub_sub_target": {
                "topic_name": f"projects/{project_id}/topics/{topic_id}",
                "data": "ping task",
                "attributes": {
                    "name": task_config["name"],
                    "url": task_config["url"],
                }
            }
        }

        # Make the request
        response = client.create_job(request={"parent": parent, "job": job})

        config["job_name"] = response.name

        # Handle the response
        print(response)

def create_topic() -> None:
    """Create a new Pub/Sub topic."""
    # [START pubsub_quickstart_create_topic]
    # [START pubsub_create_topic]

    project_id = os.environ.get('PROJECT_ID')
    topic_id = os.environ.get('TOPIC_ID')

    topic_path = publisher.topic_path(project_id, topic_id)
    topic = publisher.create_topic(request={"name": topic_path})

    print(f"Created topic: {topic.name}")
    # [END pubsub_quickstart_create_topic]
    # [END pubsub_create_topic]

if __name__ == "__main__":
    load_dotenv()
    config = parse_config()
    print(config)
    create_topic()
    set_tasks()

    logging.basicConfig(level=logging.INFO)
    asyncio.get_event_loop().run_until_complete(serve())