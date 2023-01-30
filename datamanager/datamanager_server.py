import logging
from concurrent import futures

from multiprocessing import Process, Lock
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


def update_config(
    name: str,
    domain: str,
    frequency: int,
    alerting_window: int,
    allowed_response_time: int,
    email1: str,
    email2: str,
):
    with Session(engine) as session:

        # update service
        service = Services(
            name=name,
            domain=domain,
            frequency=frequency,
            alerting_window=alerting_window,
            allowed_response_time=allowed_response_time,
        )

        old = session.query(Services).where(Services.name == name).first()
        if old:
            old.frequency = frequency
            old.domain = domain
            old.alerting_window = alerting_window
            old.allowed_response_time = allowed_response_time
            session.add(old)
            service = old
        else:
            session.add(service)

        # update admins
        admin1 = Admins(email=email1)
        admin2 = Admins(email=email2)

        old1 = session.query(Admins).where(Admins.email == email1).first()
        odl2 = session.query(Admins).where(Admins.email == email2).first()

        if not old1:
            session.add(admin1)

        if not odl2:
            session.add(admin2)

        # delete ownership
        ownerships = (
            session.query(Ownership).where(Ownership.service_id == service.id).all()
        )
        for ownership in ownerships:
            session.delete(ownership)

        session.commit()

        # update ownership
        admin1 = session.query(Admins).where(Admins.email == email1).first()
        admin2 = session.query(Admins).where(Admins.email == email2).first()
        service = session.query(Services).where(Services.name == service.name).first()
        session.merge(
            Ownership(service_id=service.id, admin_id=admin1.id, first_contact=True)
        )
        session.merge(
            Ownership(service_id=service.id, admin_id=admin2.id, first_contact=False)
        )

        session.commit()


# Inherit from example_pb2_grpc.ExampleServiceServicer
# ExampleServiceServicer is the server-side artifact.
class DataManager(datamanager_pb2_grpc.DataManagerServicer):
    def ChangeConfig(
        self, request: datamanager_pb2.ServiceConfig, _context: grpc.ServicerContext
    ):
        update_config(
            name=request.name,
            domain=request.url,
            frequency=request.frequency,
            alerting_window=request.alerting_window,
            allowed_response_time=request.allowed_resp_time,
            email1=request.email1,
            email2=request.email2,
        )

        return datamanager_pb2.ResponseMsg(result="okay")


def run_in_cycle():
    try:
        while True:
            with Session(engine) as session:

                lock.acquire()
                stmt = select(Services)
                services = session.exec(stmt).all()

                for service in services:
                    if not (service.name in config):
                        config[service.name] = {
                            "service_id": service.id,
                            "url": service.domain,
                            "frequency": service.frequency,
                            "last_ping": int(round(datetime.now().timestamp())),
                            "enabled": True,
                        }
                    else:
                        config[service.name] = {
                            "service_id": service.id,
                            "url": service.domain,
                            "frequency": service.frequency,
                            "last_ping": config[service.name]["last_ping"],
                            "enabled": True,
                        }
                lock.release()

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
                if (config[name]["enabled"]) and (
                    cycle_ts >= config[name]["last_ping"]
                ):

                    config[name]["last_ping"] += config[name]["frequency"]

                    record = {
                        "service_id": config[name]["service_id"],
                        "domain": config[name]["url"],
                    }

                    data = json.dumps(record).encode("utf-8")
                    _future = publisher.publish(topic_path, data)
                    # logging.info(f'published message id {future.result()}')

                    serv_id = config[name]["service_id"]
                    urll = config[name]["url"]

                    logging.info(f"HELLO FROM {name} {serv_id} {urll}")

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
    global lock
    config = {}
    lock = Lock()

    proc = Process(target=run_in_cycle)
    proc.start()

    # thread = Thread(target=run_in_cycle)
    # thread.start()

    bind_address = f"[::]:{port}"
    server = grpc.server(futures.ThreadPoolExecutor())
    datamanager_pb2_grpc.add_DataManagerServicer_to_server(DataManager(), server)

    server.add_insecure_port(bind_address)
    server.start()
    logging.info("Listening on port %s.", port)
    server.wait_for_termination()


if __name__ == "__main__":
    port = os.environ.get("PORT", "50051")
    logging.basicConfig(level=logging.INFO)
    serve(port)
