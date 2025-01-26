"""
REST API example for the smart-meter
"""

import requests
from dataclasses import fields
import time
from typing import Type
from src.mssg import Reading


def filter_json_data(json_data: dict, dataclass_type: Type[Reading]) -> dict:
    """
    Filters the input JSON dictionary to include only the fields defined in the dataclass.
    """
    dataclass_field_names = {field.name for field in fields(dataclass_type)}
    return {
        key: value for key, value in json_data.items() if key in dataclass_field_names
    }


if __name__ == "__main__":
    # Define the URL of the REST-API server
    url = "http://192.168.2.11:82/smartmeter/api/read"

    response = requests.get(url)
    if response.status_code == 200:
        json_data = response.json()
        filtered_data = filter_json_data(json_data, Reading)  # Filter out unwanted keys
        reading_instance = Reading(**filtered_data)
        print(reading_instance)
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")

    received_message = Reading(**json_data)

    # %%
    while True:
        try:
            # Send a GET request to the server
            response = requests.get(url)

            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                # Parse the response as JSON
                json_data = response.json()
                # print("Successfully retrieved data:")
                # print(json_data)
            else:
                print(f"Failed to retrieve data. Status code: {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")

        print(f"Power: {float(json_data['PowerDelivered_total']):.3f}")
        time.sleep(3)
