# Datamanager

In this repo we extracted the part of the system that is responsible for handling user config changes and generating ping tasks.

- ### Datamanager

It has to have only one instance (min and max), because it is responsible for genereating tasks and initiation task generator, so it has to be stateless to handle timestamps to know if next task has to be sent to queue.

- ### Datamanager-API


---

## Local setup

One has to define following env variables (example of an .env file, specific values may differ):

```bash
INSTANCE_UNIX_SOCKET=xxxxxxxx
INSTANCE_CONNECTION_NAME=xxxxxxxx
DB_NAME=alerts
DB_USER=postgres
DB_PASS=xxxxxxxx
DB_PORT=5432
PROJECT_ID=xxxxxxxx
TOPIC_ID=xxxxxxxx
DM_SERVER_URL=xxxxxxxx
```

### Build

```bash
docker build datamanager -t datamanager:latest
docker build datamanager-api -t datamanager-api:latest
```

### Run

```
docker run -d -p 50054:50054  --env-file .env datamanager:latest
docker run -d  --env-file .env datamanager-api:latest
```

---

## Cloud run setup

Env variables for docker containers:

```yaml
INSTANCE_UNIX_SOCKET: xxxxxxxx
INSTANCE_CONNECTION_NAME: cxxxxxxxx
DB_NAME: alerts
DB_USER: postgres
DB_PASS: xxxxxxxx
PROJECT_ID: xxxxxxxx
TOPIC_ID: xxxxxxxx
DM_SERVER_URL: xxxxxxxx
```

Env variables for deployment:

```bash
GCP_PROJECT_ID=xxx # Google cloud project id e.g. cloudruntest-123456
DATAMANAGER_IMAGE_NAME=xxx
DATAMANAGER_API_IMAGE_NAME=xxx
GCP_DATAMANAGER_APP_NAME
GCP_DATAMANAGER_API_NAME
```

### Build

Build docker images and push them to the container registry:

```bash
./scripts/build-docker.sh datamanager $DATAMANAGER_IMAGE_NAME
./scripts/build-docker.sh datamanager-api $DATAMANAGER_API_IMAGE_NAME
```

### Deploy

When deploying for the first time there are a few caveats:

- We cannot deduce endpoints of each service before they are deployed for the first time.
  Hence, we will need to update those values after first failed deployment.
- We have to set necessary secrets/env variables for each service. Next revisions will inherit those variables, so it is only one time hassle.

```bash
gcloud run deploy $DATAMANAGER_APP_NAME \
--image $DATAMANAGER_IMAGE_NAME \
--region europe-north1 \
--platform managed \
--allow-unauthenticated \
--min-instances 1 \
--max-instances 1 \
--env-vars-file .env.yaml \
--add-cloudsql-instances $CLOUD_INSTANCE \
--no-cpu-throttling \
```

```bash
gcloud run deploy $DATAMANAGER_API_NAME \
--image $DATAMANAGER_API_IMAGE_NAME \
--region europe-north1 \
--platform managed \
--allow-unauthenticated \
--env-vars-file .env.yaml \
--min-instances 1
```
