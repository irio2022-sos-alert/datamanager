#!/bin/bash
readonly service="$1"
readonly image_name="$2"

docker build $service -t $image_name
docker push $image_name