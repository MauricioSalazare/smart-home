"""
REST API for the smart-meter of my home
"""

import requests
import time
# Define the URL of the REST-API server
url = "http://192.168.2.11:82/smartmeter/api/read"

#%%
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