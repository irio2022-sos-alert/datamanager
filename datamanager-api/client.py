from fastapi import FastAPI

import datamanager_client

client = datamanager_client.ExampleDataManagerClient()
from sqlmodel import Session
from db import engine
from models import Services, Admins, Ownership


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


app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/change_service/{name}")
def read_item(
    name: str,
    url: str,
    frequency: int,
    alerting_window: int,
    allowed_resp_time: int,
    email1: str,
    email2: str,
):
    update_config(
        name, url, frequency, alerting_window, alerting_window, email1, email2
    )
