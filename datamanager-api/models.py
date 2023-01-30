from sqlmodel import Field, SQLModel
from datetime import datetime


class Services(SQLModel, table=True):
    _tablename_ = "services"
    id: int = Field(primary_key=True)
    name: str = Field(unique=True)
    domain: str
    frequency: int
    alerting_window: int
    allowed_response_time: int


class Responses(SQLModel, table=True):
    _tablename_ = "responses"
    service_id: int = Field(foreign_key="services.id", primary_key=True)
    timestamp: float


class Admins(SQLModel, table=True):
    _tablename_ = "admins"
    id: int = Field(primary_key=True)
    email: str


class Ownership(SQLModel, table=True):
    _tablename_ = "ownership"
    service_id: int = Field(foreign_key="services.id", primary_key=True)
    admin_id: int = Field(foreign_key="admins.id", primary_key=True)
    first_contact: bool


class Alerts(SQLModel, table=True):
    _tablename_ = "alerts"
    service_id: int = Field(foreign_key="services.id", primary_key=True)
    deadline: datetime