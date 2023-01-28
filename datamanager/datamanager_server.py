import logging
from concurrent import futures

from threading import Thread, Event
import time
from datetime import datetime

import os
import json

import grpc
import datamanager_pb2
import datamanager_pb2_grpc

from db import init_connection_pool, migrate_db
from models import Services
from sqlmodel import Session, select

from google.cloud import pubsub_v1

# Inherit from example_pb2_grpc.ExampleServiceServicer
# ExampleServiceServicer is the server-side artifact.
class DataManager(datamanager_pb2_grpc.DataManagerServicer): 
    def ChangeConfig(self, 
                    request: datamanager_pb2.ServiceConfig, 
                    _context: grpc.ServicerContext):

        with Session(engine) as session:
            name = request.name
            services = session.query(Services).get(name)

            try:
                service = services.one()
                service.url = request.url
                service.frequency = request.frequency
                service.alerting_window = request.name,
                service.allowed_resp_time = request.name

                session.add(service)
                session.commit()
            except:
                service = Services(
                        name=request.name, 
                        url = request.url,
                        frequency = request.frequency,
                        alerting_window = request.name,
                        allowed_resp_time = request.name,
                        email = request.email
                    )
                
                session.add(service)
                session.commit()

        return datamanager_pb2.ResponseMsg(result="okay")

    def StopService(self, 
                    request: datamanager_pb2.ServiceName, 
                    _context: grpc.ServicerContext):
        
        # with Session(engine) as session:
        #     name = request.name
        #     service = session.query(Services).get(name)

        #     session.delete(service)
        #     session.commit()

        # config[request.name]["enabled"] = False

        return datamanager_pb2.ResponseMsg(result="not supported for now")

def run_in_cycle():
    while True:
        with Session(engine) as session:
            stmt = select(Services)
            services = session.exec(stmt)

            for service in services:
                if not (service.name in config):
                    config[service.name] = {
                        "service_id": service.id,
                        "url": service.url, 
                        "frequency": service.frequency,
                        "last_ping": int(round(datetime.now().timestamp()))
                    }

        cycle_ts = int(round(datetime.now().timestamp()))
        publisher = pubsub_v1.PublisherClient()
        project_id = os.getenv("PROJECT_ID")
        topic_id = os.getenv("TOPIC_ID")
        topic_path = publisher.topic_path(project_id, topic_id)

        for name in config:
            if cycle_ts >= config[name]["last_ping"]:

                config[name]["last_ping"] += config[name]["frequency"]

                record = {
                    'service_id': config[name]["service_id"],
                    'domain': config[name]["url"],
                    #TODO: nie wiem czy Kamil nie chciał jeszcze jakiegoś pola
                }

                data = json.dumps(record).encode("utf-8")
                _future = publisher.publish(topic_path, data)
                # logging.info(f'published message id {future.result()}')

                logging.info("HELLO FROM %s", name)


        time.sleep(service.frequency)

def init_db():
    global engine
    engine = init_connection_pool()
    migrate_db(engine)

def serve(port) -> None:

    global config
    config = {}

    bind_address = f"[::]:{port}"
    server = grpc.server(futures.ThreadPoolExecutor())
    datamanager_pb2_grpc.add_DataManagerServicer_to_server(
        DataManager(), server
    )

    server.add_insecure_port(bind_address)
    server.start()

    thread = Thread(target=run_in_cycle)
    thread.start()

    logging.info("Listening on port %s.", port)
    server.wait_for_termination()


if __name__ == "__main__":
    port = os.environ.get("PORT", "50051")
    logging.basicConfig(level=logging.INFO)
    serve(port)
