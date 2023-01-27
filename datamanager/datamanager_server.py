import logging
from concurrent import futures

from threading import Thread, Event
import time

import os
import json

import grpc
import datamanager_pb2
import datamanager_pb2_grpc

# from db import init_connection_pool, migrate_db
# from models import Services
# from sqlmodel import Session

from google.cloud import pubsub_v1

config = {}

# Inherit from example_pb2_grpc.ExampleServiceServicer
# ExampleServiceServicer is the server-side artifact.
class DataManager(datamanager_pb2_grpc.DataManagerServicer): 
    def ChangeConfig(self, 
                    request: datamanager_pb2.ServiceConfig, 
                    _context: grpc.ServicerContext):

        # with Session(engine) as session:
        #     name = request.name
        #     service = session.query(Services).get(name)

        #     service.url = request.url
        #     service.frequency = request.frequency
        #     service.alerting_window = request.name,
        #     service.allowed_resp_time = request.name

        #     session.add(service)
        #     session.commit()

        if not config[request.name]["enabled"]:
            thread = Thread(target=run_in_cycle, args=(request.name))
            thread.start()

        config[request.name]["url"] = request.url
        config[request.name]["frequency"] = request.frequency
        config[request.name]["enabled"] = True

        return datamanager_pb2.ResponseMsg(result="okay")

    def StopService(self, 
                    request: datamanager_pb2.ServiceName, 
                    _context: grpc.ServicerContext):
        
        # with Session(engine) as session:
        #     name = request.name
        #     service = session.query(Services).get(name)

        #     session.delete(service)
        #     session.commit()

        config[request.name]["enabled"] = False

        return datamanager_pb2.ResponseMsg(result="stopped")

# def run_in_cycle(name):
#     while True:
#         with Session(engine) as session:
#             service = session.query(Services).get(name)
#             if service is None:
#                 logging.info(
#                     f"Invalid confirmation request for {name}, no such service name"
#                 )
#                 break
#             else:
#                 publisher = pubsub_v1.PublisherClient()
#                 project_id = os.getenv("PROJECT_ID")
#                 topic_id = os.getenv("TOPIC_ID")
#                 topic_path = publisher.topic_path(project_id, topic_id)

#                 record = {
#                     'url': service.url,
#                 }

#                 data = json.dumps(record).encode("utf-8")
#                 future = publisher.publish(topic_path, data)
#                 logging.info(f'published message id {future.result()}')

#                 logging.info("HELLO FROM %s", service.name)
#                 time.sleep(service.frequency)

def run_in_cycle(name):
    while True:
        if not config[name]["enabled"]:
            break
        publisher = pubsub_v1.PublisherClient()
        project_id = os.getenv("PROJECT_ID")
        topic_id = os.getenv("TOPIC_ID")
        topic_path = publisher.topic_path(project_id, topic_id)

        record = {
            'url': config[name]["url"],
        }

        data = json.dumps(record).encode("utf-8")
        future = publisher.publish(topic_path, data)
        logging.info(f'published message id {future.result()}')

        logging.info("HELLO FROM %s", name)
        time.sleep(config[name]["frequency"])

# def init_db():
#     global engine
#     engine = init_connection_pool()
#     migrate_db(engine)


# def register_service(config):
#     with Session(engine) as session:
#         session.add(
#             Services(
#                 name = config["name"],
#                 url = config["url"],
#                 frequency = config["frequency"],
#                 alerting_window = config["alerting_window"],
#                 allowed_resp_time = config["allowed_resp_time"]
#             )
#         )
#         session.commit()


def parse_config() -> None:
    data = ""
    with open("config.json") as config_file:
        data = json.load(config_file)

    # for service in data:
    #     register_service(service)

    for service in data:
        config[service["name"]] = {
            "url": service["url"], 
            "frequency": service["frequency"],
            "enabled": True
        }

    for service in data:
        thread = Thread(target=run_in_cycle, args=(service["name"]))
        thread.start()


def serve(port) -> None:
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


if __name__ == "__main__":
    port = os.environ.get("PORT", "50051")
    logging.basicConfig(level=logging.INFO)
    serve(port)
