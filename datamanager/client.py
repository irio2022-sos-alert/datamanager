from fastapi import FastAPI

import datamanager_client

client = datamanager_client.ExampleDataManagerClient()

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
        email: str 
        ):
    cfg =  {
        "name": name,
        "url": url,
        "frequency": frequency,
        "alerting_window": alerting_window,
        "allowed_resp_time": allowed_resp_time,
        "email": email
    }

    client.change_config(cfg)