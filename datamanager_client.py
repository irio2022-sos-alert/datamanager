import grpc
import datamanager_pb2
import datamanager_pb2_grpc


SERVER_ADDRESS = 'localhost'
PORT = 50051

class ExampleDataManagerClient(object):
    def __init__(self):
        self.channel = grpc.insecure_channel(f'{SERVER_ADDRESS}:{PORT}')
        self.stub = datamanager_pb2_grpc.DataManagerStub(self.channel)
    
    def get_service(self, name):
        request = datamanager_pb2.GetServiceRequest(
            name=name
        )

        try:
            response = self.stub.GetService(request)
            print('Service fetched.')
            print(response)
        except grpc.RpcError as err:
            print(err.details())
            print('{}, {}'.format(err.code().name, err.code().value))

    def change_config(self, cfg):
        request = datamanager_pb2.ServiceConfig(
            name=cfg["name"],
            url=cfg["url"],
            frequency=cfg["frequency"],
            alerting_window=cfg["alerting_window"],
            allowed_resp_time=cfg["allowed_resp_time"],
            phone_number=cfg["phone_number"],
            email=cfg["email"]
        )

        try:
            response = self.stub.ChangeConfig(request)
            print('New config sent.')
            print(response)
        except grpc.RpcError as err:
            print(err.details())
            print('{}, {}'.format(err.code().name, err.code().value))