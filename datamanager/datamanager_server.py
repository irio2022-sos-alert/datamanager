import logging
from concurrent import futures

from multiprocessing import Process
import psutil
import sys

import time
from datetime import datetime

import os
import json

import grpc
import datamanager_pb2
import datamanager_pb2_grpc

from db import init_connection_pool, migrate_db
from models import Services, Admins, Ownership, Alerts, Responses
from sqlmodel import Session, select

from google.cloud import pubsub_v1

# Inherit from example_pb2_grpc.ExampleServiceServicer
# ExampleServiceServicer is the server-side artifact.
class DataManager(datamanager_pb2_grpc.DataManagerServicer): 
    def ChangeConfig(self, 
                    request: datamanager_pb2.ServiceConfig, 
                    _context: grpc.ServicerContext):
        with Session(engine) as session:
            name=request.name

            services=session.query(Services).where(Services.name == name).all()


            if len(services) == 1:
                service=services[0]
                service.domain=request.url
                service.frequency=request.frequency
                service.alerting_window=request.alerting_window
                service.allowed_response_time=request.allowed_resp_time

                session.add(service)
            else:
                service = Services(
                        name=request.name, 
                        domain=request.url,
                        frequency=request.frequency,
                        alerting_window=request.alerting_window,
                        allowed_response_time=request.allowed_resp_time
                    )
                
                session.add(service)

            services=session.query(Services).where(Services.name == name)
            service_id = services.one().id

            ownerships = session.query(Ownership).where(Ownership.service_id == service_id).all()
            for ownership in ownerships:
                session.delete(ownership)
            # session.query(Ownership).where(Ownership.service_id == service_id)

            
            admins=session.query(Admins).where(Admins.email == request.email1).all()
            if len(admins) == 1:
                admin1_id=admins[0].id

                ownership1 = Ownership(
                        service_id=service_id,
                        admin_id=admin1_id,
                        first_contact=True
                    )

                session.add(ownership1)

            else:
                admin1 = Admins(
                        email=request.email1
                    )
                session.add(admin1)
                admin1_id = session.query(Admins).where(Admins.email == request.email1).one().id

                ownership1 = Ownership(
                        service_id=service_id,
                        admin_id=admin1_id,
                        first_contact=True
                    )

                session.add(ownership1)
        
            admins = session.query(Admins).where(Admins.email == request.email2).all()
            if len(admins) == 1:
                admin2_id = admins[0].id

                ownership2 = Ownership(
                        service_id=service_id,
                        admin_id=admin2_id,
                        first_contact=False
                    )

                session.add(ownership2)

            else:
                admin2 = Admins(
                        email=request.email2
                    )
                session.add(admin2)
                admin2_id = session.query(Admins).where(Admins.email == request.email2).one().id

                ownership2 = Ownership(
                        service_id=service_id,
                        admin_id=admin2_id,
                        first_contact=False
                    )

                session.add(ownership1)

            session.commit()

        return datamanager_pb2.ResponseMsg(result="okay")

def run_in_cycle():
    try:
        while True:
            with Session(engine) as session:
                stmt = select(Services)
                services = session.exec(stmt).all()

                for service in services:
                    if not (service.name in config):
                        config[service.name] = {
                            "service_id": service.id,
                            "url": service.domain, 
                            "frequency": service.frequency,
                            "last_ping": int(round(datetime.now().timestamp())),
                            "enabled" : True
                        }
                    else:
                        config[service.name] = {
                            "service_id": service.id,
                            "url": service.domain, 
                            "frequency": service.frequency,
                            "last_ping": config[service.name]["last_ping"],
                            "enabled" : True
                        }

                services_names = [service.name for service in services]

                keys = config.keys()
                for key in keys:
                    if key not in services_names:
                        del config[key]
                    

            cycle_ts = int(round(datetime.now().timestamp()))
            publisher = pubsub_v1.PublisherClient()
            project_id = os.getenv("PROJECT_ID")
            topic_id = os.getenv("TOPIC_ID")
            topic_path = publisher.topic_path(project_id, topic_id)

            for name in config:
                if (config[name]["enabled"]) and (cycle_ts >= config[name]["last_ping"]):

                    config[name]["last_ping"] += config[name]["frequency"]

                    record = {
                        'service_id': config[name]["service_id"],
                        'domain': config[name]["url"]
                    }

                    data = json.dumps(record).encode("utf-8")
                    _future = publisher.publish(topic_path, data)
                    # logging.info(f'published message id {future.result()}')

                    logging.info("HELLO FROM %s", name)


            time.sleep(0.05)
    except:
        p = psutil.Process(os.getppid())
        p.terminate()
        sys.exit()

def init_db():
    global engine
    engine = init_connection_pool()
    migrate_db(engine)

def serve(port) -> None:

    init_db()

    global config
    config = {}

    proc = Process(target=run_in_cycle)
    proc.start()

    # thread = Thread(target=run_in_cycle)
    # thread.start()

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
