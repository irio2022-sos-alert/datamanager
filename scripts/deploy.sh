#!/bin/bash

readonly app_name="$1"
readonly image_name="$2"
readonly cloudsql_instance="$3"

gcloud run deploy $app_name \
--image $image_name \
--region europe-north1 \
--platform managed \
--allow-unauthenticated \
--min-instances 1 \
--max-instances 1 \
--env-vars-file .env.yaml \
--add-cloudsql-instances $cloudsql_instance \
--no-cpu-throttling \