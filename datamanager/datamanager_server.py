import logging
from concurrent import futures
import asyncio

import grpc
import datamanager_pb2
import datamanager_pb2_grpc

from google.cloud import pubsub_v1

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

async def serve(port) -> None:
    await create_topic()
    bind_address = f"[::]:{port}"
    server = grpc.server(futures.ThreadPoolExecutor())
    datamanager_pb2_grpc.add_DataManagerServicer_to_server(
        DataManager(), server
    )

    server.add_insecure_port(bind_address)
    server.start()
    logging.info("Listening on %s.", bind_address)
    await server.wait_for_termination()

async def create_topic() -> None:
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


async def main():
    port = os.environ.get("PORT", "50051")
    logging.basicConfig(level=logging.INFO)
    await serve(port)

if __name__ == "__main__":
    asyncio.run(main())