#!/bin/bash

readonly id="$1"
readonly topic="$2"
readonly endpoint="$3"

gcloud pubsub subscriptions create $id --topic $topic --push-endpoint $endpoint || true