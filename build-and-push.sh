#!/bin/bash

docker buildx create --use 2>/dev/null || true
docker buildx build --platform linux/amd64,linux/arm64 -t salazaem/smart-meter-mqtt:latest --push .

