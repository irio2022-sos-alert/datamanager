#!/bin/bash

readonly topic="$1"

gcloud pubsub topics create $topic || true