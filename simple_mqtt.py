"""
Simple MQTT script to read the smart meter data.
"""


import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

if __name__ == "__main__":
    # MQTT broker details
    BROKER = os.getenv("BROKER_IP")
    PORT = int(os.getenv("PORT", 1883))  # Default to 1883 if not set
    USERNAME = os.getenv("USERNAME")
    PASSWORD = os.getenv("PASSWORD")
    ROOT_TOPIC = os.getenv("TOPIC_ELECTRICITY")

    # Dictionary to store the subtopic and its latest value


    # Callback when the client successfully connects to the broker
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to broker!")
            # Subscribe to the root topic
            client.subscribe(ROOT_TOPIC)
            print(f"Subscribed to topic: {ROOT_TOPIC}")
        else:
            print(f"Failed to connect, return code {rc}")


    # Callback when a message is received
    def on_message(client, userdata, msg):
        # Extract the subtopic (remove 'dsmr/reading/' from the topic)
        subtopic = msg.topic.replace("dsmr/reading/", "")
        # Update the dictionary
        data = msg.payload.decode()
        # Print the updated dictionary
        print(f"Updated data: {data}, {subtopic}")


    # Create an MQTT client instance
    client = mqtt.Client()

    # Set username and password
    client.username_pw_set(USERNAME, PASSWORD)

    # Assign callbacks
    client.on_connect = on_connect
    client.on_message = on_message

    # Connect to the broker
    client.connect(BROKER, PORT, 60)

    # Start the MQTT client loop
    client.loop_forever()
