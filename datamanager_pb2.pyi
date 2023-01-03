from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class GetServiceRequest(_message.Message):
    __slots__ = ["name"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class ServiceConfig(_message.Message):
    __slots__ = ["alerting_window", "allowed_resp_time", "email", "frequency", "name", "phone_number", "url"]
    ALERTING_WINDOW_FIELD_NUMBER: _ClassVar[int]
    ALLOWED_RESP_TIME_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    FREQUENCY_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PHONE_NUMBER_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    alerting_window: int
    allowed_resp_time: int
    email: str
    frequency: int
    name: str
    phone_number: str
    url: str
    def __init__(self, name: _Optional[str] = ..., url: _Optional[str] = ..., frequency: _Optional[int] = ..., alerting_window: _Optional[int] = ..., allowed_resp_time: _Optional[int] = ..., phone_number: _Optional[str] = ..., email: _Optional[str] = ...) -> None: ...
