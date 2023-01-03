import asyncio
import logging

import grpc
import datamanager_pb2
import datamanager_pb2_grpc

from google.protobuf import empty_pb2

import json


config = {}

# Inherit from example_pb2_grpc.ExampleServiceServicer
# ExampleServiceServicer is the server-side artifact.
class DataManagerServicer(datamanager_pb2_grpc.DataManagerServicer): 
    def GetService(self, request, context):
        """ Gets a service. """
        name = request.name

        service = config[name]

        service_config = datamanager_pb2.ServiceConfig(
            name = service["name"],
            url = service["url"],

            frequency = service["frequency"],
            alerting_window = service["alerting_window"],
            allowed_resp_time = service["allowed_resp_time"],

            phone_number = service["phone_number"],
            email = service["email"]
        )

        return service_config

    def ChangeConfig(self, request, context):

        name = request.name

        dic = {
            "name": request.name,
            "url": request.url,
            "frequency": request.frequency,
            "alerting_window": request.alerting_window,
            "allowed_resp_time": request.allowed_resp_time,
            "phone_number": request.phone_number,
            "email": request.email
        }

        config[name] = dic

        return empty_pb2.Empty()

def parse_config() -> dict:
    dic = {}
    data = ""
    with open("config.json") as config_file:
        data = json.load(config_file)

    for service in data:
        dic[service["name"]] = service

    return dic

async def serve() -> None:
    server = grpc.aio.server()
    datamanager_pb2_grpc.add_DataManagerServicer_to_server(
        DataManagerServicer(), server
    )

    server.add_insecure_port("[::]:50051")
    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    config = parse_config()
    print(config)

    logging.basicConfig(level=logging.INFO)
    asyncio.get_event_loop().run_until_complete(serve())