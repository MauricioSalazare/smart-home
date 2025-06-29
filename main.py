import paho.mqtt.client as mqtt
from datetime import datetime, timezone
from threading import Timer, Event
import threading
from dotenv import load_dotenv
import os
from typing import Optional
from src.mssg import Message
from src.db import DBConnection
from src.logger import setup_logger



logger = setup_logger(__name__)
# Load environment variables from the .env file

load_dotenv()

# MQTT broker details
BROKER = os.getenv("BROKER_IP")
PORT = int(os.getenv("PORT", 1883))  # Default to 1883 if not set
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
TOPICS = [
    (os.getenv("TOPIC_ELECTRICITY"), 0),
    (os.getenv("TOPIC_GAS"), 0),
]  # List of topics to subscribe to with QoS level

# Database configuration
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "table": os.getenv("DB_TABLE"),
}


class MQTTHandler:
    """Handles MQTT subscriptions and stores specific data into a database."""

    def __init__(
        self,
        broker: str,
        port: int,
        username: str,
        password: str,
        topics: list | str,
        db_handler: Optional[DBConnection] = None,
        timeout: int = 7,  # seconds
    ):

        self.db_handler = db_handler

        # Check TimescaleDB extension is installed
        self.db_handler.check_timescaledb()
        # Check if the table exist. Otherwise, create the TimescaleDB hypertable.
        self.db_handler.create_hypertable(
            Message, index_columns=["electricity_currently_delivered"]
        )

        # MQTT credentials
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password

        if isinstance(topics, str):
            topics = [(topics, 0)]

        self.root_topics = topics
        self.timeout = timeout

        self.current_message: Message = (
            Message()
        )  # Single instance of Message to track subtopics

        self.timer = None
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.will_set("clients/python_status", payload="disconnected", qos=1, retain=True)
        self.stop_event = Event()
        self.setup_mqtt_client()

    def setup_mqtt_client(self):
        """Sets up the MQTT client callbacks."""
        self.mqtt_client.username_pw_set(self.username, self.password)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_disconnect = self.on_disconnect

    def on_connect(self, client, userdata, flags, rc):
        """Callback when the MQTT client connects to the broker."""
        if rc == 0:
            print("Connected to broker!")
            print(f"Connected to {self.broker}:{self.port} as {self.username}")
            logger.info(f"Connected to {self.broker}:{self.port} as {self.username}")

            for topic, qos in self.root_topics:
                if topic:
                    client.subscribe(topic, qos)
                    print(f"Subscribed to topic: {topic} with qos: {qos}")
                    logger.info(f"Subscribed to topic: {topic} with qos: {qos}")
                else:
                    print("Warning: Empty topic detected. Check .env file!")
                    logger.warning("Warning: Empty topic detected. Check .env file!")

        else:
            print(f"Failed to connect, return code {rc}")

    def on_disconnect(self, client, userdata, rc):
        """Callback when the MQTT client is disconnected."""
        print(f"Disconnected from broker with code {rc}")
        logger.info(f"Disconnected from broker with code {rc}")

        # if rc != 0:
        #     print("Unexpected disconnection. Reconnecting...")
        while not self.stop_event.is_set():
            try:
                print("Attempting to reconnect...")
                logger.info(f"Attempting to reconnect...")
                self.mqtt_client.reconnect()
                logger.info("Reconnected successfully! Exiting on_disconnect().")
                print("Reconnected successfully! Exiting on_disconnect().")
                return
            except Exception as e:
                logger.info(f"Reconnection failed: {e}. Retrying in 5 seconds...")
                print(f"Reconnection failed: {e}. Retrying in 5 seconds...")
                self.stop_event.wait(5)

    def on_message(self, client, userdata, msg):
        """Callback when a message is received."""

        try:

            print(f"Received message on topic: {msg.topic} with payload: {msg.payload.decode()}")

            subtopic = None
            for root_topic, _ in self.root_topics:
                clean_topic = root_topic.replace("#", "")  # Remove wildcard
                if msg.topic.startswith(clean_topic):
                    subtopic = msg.topic.replace(clean_topic, "")
                    break

            if subtopic is None:
                print(f"Received message from unknown topic: {msg.topic}")
                return

            payload = msg.payload.decode()

            # Update the corresponding field in the current message
            if hasattr(self.current_message, subtopic):
                setattr(self.current_message, subtopic, payload)
                print(f"Updated field: {subtopic} -> {payload}")

            # Reset the timeout RRtimer
            if self.timer:
                self.timer.cancel()
            self.timer = Timer(self.timeout, self.handle_timeout)
            self.timer.start()

            # Check if the message is complete and save it to the database
            if self.current_message.is_complete():
                self.current_message.timestamp_utc = datetime.now(timezone.utc).replace(
                    microsecond=0
                )
                if self.db_handler is not None:
                    self.db_handler.save_message(self.current_message)
                    print(f"Saved complete message: {self.current_message}")
                else:
                    print(f"Complete message: {self.current_message}")
                self.reset_message()

        except Exception as e:
            logger.error(f"Error while handling message: {e}")
            print(f"Error processing message: {e}")

    def handle_timeout(self):
        """Handle timeout for incomplete messages."""
        print("Timeout reached! Saving partial message to the database.")
        self.current_message.timestamp_utc = datetime.now(timezone.utc).replace(
            microsecond=0
        )
        self.db_handler.save_message(self.current_message)
        self.reset_message()

    def reset_message(self):
        """Reset the current message and stop the timer."""
        if self.timer:
            self.timer.cancel()
            self.timer = None
        self.current_message = Message()

        # Restart the timer to handle a new timeout
        self.timer = Timer(self.timeout, self.handle_timeout)
        self.timer.start()

    def start(self):
        """Starts the MQTT client loop."""
        try:
            # Start heartbeat in a background thread
            self.heartbeat_thread = threading.Thread(target=self.publish_heartbeat, daemon=True)
            self.heartbeat_thread.start()

            self.mqtt_client.connect(self.broker, self.port, keepalive=60)
            print("MQTT client started. Listening for messages...")
            logger.info("MQTT client started. Listening for messages...")
            self.mqtt_client.loop_forever()
        except KeyboardInterrupt:
            print("Gracefully stopping MQTT handler...")
            logger.info("Gracefully stopping MQTT handler...")
            self.stop_event.set()
            self.mqtt_client.disconnect()


    def publish_heartbeat(self):
        while not self.stop_event.is_set():
            try:
                self.mqtt_client.publish("clients/python_status", "alive", qos=1, retain=True)
                print("[HEARTBEAT] Published alive message")
            except Exception as e:
                print(f"[HEARTBEAT ERROR] {e}")
            self.stop_event.wait(300)  # every 5 minutes

# Main execution
if __name__ == "__main__":
    db_connection = DBConnection(**DB_CONFIG)
    handler = MQTTHandler(
        broker=BROKER,
        port=PORT,
        username=USERNAME,
        password=PASSWORD,
        db_handler=db_connection,
        topics=TOPICS,
        timeout=7,
    )
    handler.start()
