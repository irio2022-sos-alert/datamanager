import datamanager_client

cfg = {
    "name": "google",
    "url": "google.pl",
    "frequency": 420,
    "alerting_window": 420,
    "allowed_resp_time": 420,
    "phone_number": "987654321",
    "email": "google@gmail.pl"
}

client = datamanager_client.ExampleDataManagerClient()

client.get_service('google')
client.change_config(cfg)
client.get_service('google')