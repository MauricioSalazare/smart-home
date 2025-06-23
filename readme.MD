# Smart-home project
Read the smart meter data using [Smart meter gateways](https://smartgateways.nl/product/slimme-meter-wifi-gateway/) using
the MQTT protocol.

A Mosquitto broker is running in a NUC server. The same server is hosting a PostgresSQL database.

The read messages from the smart meter are stored in a PostgreSQL database with a TimescaleDB extension.

The docker container running the script to receive the MQTT message and push it to the database will
be hosted in a docker container. The docker image is pushed to `ghcr.io` so the server can pull it for 
'production'.

## Steps to run docker
Build the image for development purposes like
```shell
docker build -t smart-meter-mqtt .
```
Run the container de-attached with the local `.env` variables lie
```shell
docker run -d --env-file .env --name smart-meter smart-meter-mqtt
```

## Ready to deploy
Build the image for linux using the bash script like this
```shell
 ./deploy_smart_meter.sh \
  --name smart-meter-mqtt \
  --version v1.2.3 \
  --nuc-host 192.168.2.64 \
  --nuc-user nucadmin
```
This will create the image, push it to `ghcr.io` and copy the `.env` file to you remote server.

If you want to test the 'production' image. Run it locally using
```shell
docker run -d --env-file .env --network=host -p 1883:1883 --name smart-meter-mqtt smart-meter-mqtt:v1.0.0
```

## Retrieve mosquitto logs
In case of disconnect to read the logs in the mosquitto broker:
```shell
sudo journalctl -u mosquitto.service --since "2025-06-22 13:00" | less
```
or 
```shell
sudo journalctl -u mosquitto.service --since "2025-06-22 13:00" --until "2025-06-23 10:00"
```



