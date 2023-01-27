#!/bin/bash

readonly app_name="$1"
readonly image_name="$2"
readonly env="$3"

gcloud run deploy $app_name \
--image $image_name \
--region europe-north1 \
--platform managed \
--allow-unauthenticated \
--update-env-vars $env \
--no-cpu-throttling