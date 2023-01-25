import logging
from concurrent import futures
import asyncio

import grpc
import datamanager_pb2
import datamanager_pb2_grpc

from google.cloud import pubsub_v1

from threading import Thread, Event
import json
import time

import os

config = {}
publisher = pubsub_v1.PublisherClient()

# Inherit from example_pb2_grpc.ExampleServiceServicer
# ExampleServiceServicer is the server-side artifact.
class DataManager(datamanager_pb2_grpc.DataManagerServicer): 
    
    def ChangeConfig(self, 
                    request: datamanager_pb2.ServiceConfig, 
                    context: grpc.ServicerContext):
        

        return datamanager_pb2.ResponseMsg(result="okay")

    def StopService(self, 
                    request: datamanager_pb2.ServiceName, 
                    context: grpc.ServicerContext):
        
        key = request["name"]
        config[key]["event"].set()

        return datamanager_pb2.ResponseMsg(result="stopped")

def serve(port) -> None:
    create_topic()
    config = parse_config()
    bind_address = f"[::]:{port}"
    server = grpc.server(futures.ThreadPoolExecutor())
    datamanager_pb2_grpc.add_DataManagerServicer_to_server(
        DataManager(), server
    )

    server.add_insecure_port(bind_address)
    server.start()
    logging.info("Listening on port %s.", port)
    server.wait_for_termination()

def create_topic() -> None:
    """Create a new Pub/Sub topic."""
    # [START pubsub_quickstart_create_topic]
    # [START pubsub_create_topic]

    project_id = "turing-terminus-374215"
    topic_id = "datamanager-dataretriever-communication"

    topic_path = publisher.topic_path(project_id, topic_id)
    topic = publisher.create_topic(request={"name": topic_path})

    print(f"Created topic: {topic.name}")
    # [END pubsub_quickstart_create_topic]
    # [END pubsub_create_topic]

def run_in_cycle(name, interval, event):
    logging.info("HELLO FROM %s", name)
    # perform task in iterations
    while True:
        time.sleep(interval)
        print(name)
        if event.is_set():
            break

def parse_config() -> dict:
    dic = {}
    data = ""
    with open("config.json") as config_file:
        data = json.load(config_file)


    for service in data:
        event = Event()
        thread = Thread(target=run_in_cycle, args=(service["name"], service["frequency"], event))
        dic[service["name"]] = {
            "config": service,
            "thread_executing": thread,
            "event": event
        }
        thread.start()

    return dic

if __name__ == "__main__":
    port = os.environ.get("PORT", "50051")
    logging.basicConfig(level=logging.INFO)
    serve(port)
