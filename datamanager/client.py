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
        email1: str,
        email2: str  
        ):
    cfg =  {
        "name": name,
        "url": url,
        "frequency": frequency,
        "alerting_window": alerting_window,
        "allowed_resp_time": allowed_resp_time,
        "email1": email1,
        "email2": email2
    }

    print(name, url, frequency, alerting_window, allowed_resp_time, email1, email2)

    client.change_config(cfg)