import os
import ssl

import sqlalchemy
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.schema import DropTable
from sqlmodel import SQLModel


@compiles(DropTable, "postgresql")
def _compile_drop_table(element, compiler, **kwargs):
    return compiler.visit_drop_table(element) + " CASCADE"


def connect_tcp_socket() -> sqlalchemy.engine.base.Engine:
    """Initializes a TCP connection pool for a Cloud SQL instance of Postgres.
    Useful for testing and, or running in a local docker container with whitelisted IP."""
    db_host = os.environ[
        "INSTANCE_HOST"
    ]  # e.g. '127.0.0.1' ('172.17.0.1' if deployed to GAE Flex)
    db_user = os.environ["DB_USER"]  # e.g. 'my-db-user'
    db_pass = os.environ["DB_PASS"]  # e.g. 'my-db-password'
    db_name = os.environ["DB_NAME"]  # e.g. 'my-database'
    db_port = os.environ["DB_PORT"]  # e.g. 5432
    connect_args = {}

    if os.environ.get("DB_ROOT_CERT"):
        db_root_cert = os.environ["DB_ROOT_CERT"]  # e.g. '/path/to/my/server-ca.pem'
        db_cert = os.environ["DB_CERT"]  # e.g. '/path/to/my/client-cert.pem'
        db_key = os.environ["DB_KEY"]  # e.g. '/path/to/my/client-key.pem'

        ssl_context = ssl.SSLContext()
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.load_verify_locations(db_root_cert)
        ssl_context.load_cert_chain(db_cert, db_key)
        connect_args["ssl_context"] = ssl_context

    pool = sqlalchemy.create_engine(
        sqlalchemy.engine.url.URL.create(
            drivername="postgresql+pg8000",
            username=db_user,
            password=db_pass,
            host=db_host,
            port=db_port,
            database=db_name,
        ),
        connect_args=connect_args,
        pool_size=5,
        max_overflow=2,
        pool_timeout=30,  # 30 seconds
        pool_recycle=1800,  # 30 minutes
    )
    return pool


def connect_unix_socket() -> sqlalchemy.engine.base.Engine:
    """Initializes a Unix socket connection pool for a Cloud SQL instance of Postgres.
    Preferred way of connecting to Cloud SQL when running on cloud run."""
    db_user = os.environ["DB_USER"]  # e.g. 'my-database-user'
    db_pass = os.environ["DB_PASS"]  # e.g. 'my-database-password'
    db_name = os.environ["DB_NAME"]  # e.g. 'my-database'
    unix_socket_path = os.environ[
        "INSTANCE_UNIX_SOCKET"
    ]  # e.g. '/cloudsql/project:region:instance'

    pool = sqlalchemy.create_engine(
        sqlalchemy.engine.url.URL.create(
            drivername="postgresql+pg8000",
            username=db_user,
            password=db_pass,
            database=db_name,
            query={"unix_sock": "{}/.s.PGSQL.5432".format(unix_socket_path)},
        ),
        pool_size=5,
        max_overflow=2,
        pool_timeout=30,  # 30 seconds
        pool_recycle=1800,  # 30 minutes
    )
    return pool


def init_connection_pool() -> sqlalchemy.engine.base.Engine:
    # use a TCP socket when INSTANCE_HOST (e.g. 127.0.0.1) is defined
    if os.environ.get("INSTANCE_HOST"):
        return connect_tcp_socket()

    # use a Unix socket when INSTANCE_UNIX_SOCKET (e.g. /cloudsql/project:region:instance) is defined
    if os.environ.get("INSTANCE_UNIX_SOCKET"):
        return connect_unix_socket()

    raise ValueError(
        "Missing database connection type. Please define one of INSTANCE_HOST, INSTANCE_UNIX_SOCKET, or INSTANCE_CONNECTION_NAME"
    )


def migrate_db(db: sqlalchemy.engine.base.Engine) -> None:
    SQLModel.metadata.create_all(db)


def clean_up_db(db: sqlalchemy.engine.base.Engine) -> None:
    SQLModel.metadata.drop_all(db)


if __name__ == "__main__":
    from models import Admins, Ownership, Services
    from sqlmodel import Session

    services_count = 1000
    engine = init_connection_pool()
    migrate_db(engine)

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
            service = (
                session.query(Services).where(Services.name == service.name).first()
            )
            session.merge(
                Ownership(service_id=service.id, admin_id=admin1.id, first_contact=True)
            )
            session.merge(
                Ownership(
                    service_id=service.id, admin_id=admin2.id, first_contact=False
                )
            )

            session.commit()

    update_config("elo", "ggg.com", 3, 10, 100, "what@mai.com", "combi@elo.com")
