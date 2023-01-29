import grpc
import datamanager_pb2
import datamanager_pb2_grpc

import os

SERVER_ADDRESS = os.getenv("DM_SERVER_URL")
PORT = 443

class ExampleDataManagerClient(object):
    def __init__(self):
        self.channel = grpc.secure_channel(SERVER_ADDRESS, grpc.ssl_channel_credentials())
        # self.channel = grpc.insecure_channel(f'{SERVER_ADDRESS}')
        self.stub = datamanager_pb2_grpc.DataManagerStub(self.channel)

    def change_config(self, cfg):
        request = datamanager_pb2.ServiceConfig(
            name=cfg["name"],
            url=cfg["url"],
            frequency=cfg["frequency"],
            alerting_window=cfg["alerting_window"],
            allowed_resp_time=cfg["allowed_resp_time"],
            email1=cfg["email1"],
            email2=cfg["email2"]
        )

        try:
            response = self.stub.ChangeConfig(request)
            print('New config sent.')
            print(response)
        except grpc.RpcError as err:
            print(err.details())
            print('{}, {}'.format(err.code().name, err.code().value))

    def stop_service(self, cfg):
        request = datamanager_pb2.ServiceName(
            name=cfg["name"]
        )

        try:
            response = self.stub.StopService(request)
            print('New config sent.')
            print(response)
        except grpc.RpcError as err:
            print(err.details())
            print('{}, {}'.format(err.code().name, err.code().value))