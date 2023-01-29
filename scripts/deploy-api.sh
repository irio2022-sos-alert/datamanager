#!/bin/bash

readonly app_name="$1"
readonly image_name="$2"

gcloud run deploy $app_name \
--image $image_name \
--region europe-north1 \
--platform managed \
--allow-unauthenticated \
--env-vars-file .env.yaml \