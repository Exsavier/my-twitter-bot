import time
import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv("keys.env")

PROPUBLICA_API_KEY = os.getenv("PROPUBLICA_API_KEY")
REQUESTS_FILE = "request_count.txt"
LAST_BILL_FILE = "last_bill_id.txt"

logging.basicConfig(level=logging.INFO)

def manage_requests():
    with open(REQUESTS_FILE, "r") as f:
        requests_made = int(f.read().strip() or "0")

    if requests_made >= 4500:
        logging.warning("Approaching the daily request limit, aborting.")
        return False

    requests_made += 1
    with open(REQUESTS_FILE, "w") as f:
        f.write(str(requests_made))

    return True

def get_last_bill_id():
    with open(LAST_BILL_FILE, "r") as f:
        return f.read().strip()

def update_last_bill_id(bill_id):
    with open(LAST_BILL_FILE, "w") as f:
        f.write(str(bill_id))

def get_most_recent_reported_bill():
    last_bill_id = get_last_bill_id()

    for _ in range(3):  # Retry up to 3 times
        if not manage_requests():
            return None

        response = requests.get(
            "https://api.propublica.org/congress/v1/118/house/bills/reported.json",
            headers={"X-API-Key": PROPUBLICA_API_KEY}
        )

        data = response.json()

        if 'status' in data and data['status'] == '500':
            logging.error(f"Internal Server Error from ProPublica API: {data}")
            time.sleep(10)  # Wait for 10 seconds before retrying
            continue

        if 'results' not in data:
            logging.error(f"Response does not contain 'results': {data}")
            return None

        if len(data['results'][0]['bills']) == 0:
            logging.info("No new bills found that have been reported by a committee")
            return None

        most_recent_bill = data['results'][0]['bills'][0]

        if most_recent_bill['bill_id'] == last_bill_id:
            logging.info("No new bills since the last check")
            return None

        update_last_bill_id(most_recent_bill['bill_id'])
        return most_recent_bill

    logging.error("Failed to fetch the most recent reported bill after 3 attempts")
    return None

if __name__ == "__main__":
    get_most_recent_reported_bill()

