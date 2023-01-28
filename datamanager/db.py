import os
import ssl

import sqlalchemy
from sqlmodel import Session, SQLModel


# def connect_tcp_socket() -> sqlalchemy.engine.base.Engine:
#     """Initializes a TCP connection pool for a Cloud SQL instance of Postgres.
#     Useful for testing and, or running in a local docker container with whitelisted IP."""
#     db_host = os.getenv("INSTANCE_HOST")  # e.g. '127.0.0.1' ('172.17.0.1' if deployed to GAE Flex)
#     db_user = os.getenv("DB_USER")  # e.g. 'my-db-user'
#     db_pass = os.getenv("DB_PASS")  # e.g. 'my-db-password'
#     db_name = os.getenv("DB_NAME")  # e.g. 'my-database'
#     db_port = os.getenv("DB_PORT")  # e.g. 5432
#     connect_args = {}

#     if os.environ.get("DB_ROOT_CERT"):
#         db_root_cert = os.environ["DB_ROOT_CERT"]  # e.g. '/path/to/my/server-ca.pem'
#         db_cert = os.environ["DB_CERT"]  # e.g. '/path/to/my/client-cert.pem'
#         db_key = os.environ["DB_KEY"]  # e.g. '/path/to/my/client-key.pem'

#         ssl_context = ssl.SSLContext()
#         ssl_context.verify_mode = ssl.CERT_REQUIRED
#         ssl_context.load_verify_locations(db_root_cert)
#         ssl_context.load_cert_chain(db_cert, db_key)
#         connect_args["ssl_context"] = ssl_context

#     pool = sqlalchemy.create_engine(
#         sqlalchemy.engine.url.URL.create(
#             drivername="postgresql+pg8000",
#             username=db_user,
#             password=db_pass,
#             host=db_host,
#             port=db_port,
#             database=db_name,
#         ),
#         connect_args=connect_args,
#         pool_size=5,
#         max_overflow=2,
#         pool_timeout=30,  # 30 seconds
#         pool_recycle=1800,  # 30 minutes
#     )
#     return pool


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
            # query={"unix_sock": unix_socket_path}
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
    # if os.environ.get("INSTANCE_HOST"):
    #     return connect_tcp_socket()

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

    db = init_connection_pool()
    migrate_db(db)