import os
import tweepy
import logging
import textwrap
from dotenv import load_dotenv
from propublica_scraper import get_most_recent_reported_bill

load_dotenv("keys.env")

API_KEY = os.getenv("API_KEY")
API_SECRET_KEY = os.getenv("API_SECRET_KEY")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")
LAST_BILL_FILE = "last_bill_id.txt"

logging.basicConfig(filename='twitter_bot_log.txt', level=logging.INFO)

def get_api_client():
    auth = tweepy.OAuthHandler(API_KEY, API_SECRET_KEY)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

    return tweepy.API(auth)

def tweet_thread(api, text, reply_to=None):
    tweet_limit = 280
    max_tweets_per_thread = 25

    for line in textwrap.wrap(text, tweet_limit)[:max_tweets_per_thread]:
        status = api.update_status(status=line, in_reply_to_status_id=reply_to, auto_populate_reply_metadata=True)
        reply_to = status.id

    if len(textwrap.wrap(text, tweet_limit)) > max_tweets_per_thread:
        logging.warning("Text was too long to fit in a single thread, some text was not posted")

    return reply_to

def main():
    api = get_api_client()

    # Load the last tweeted bill ID
    with open(LAST_BILL_FILE, "r") as f:
        last_bill_id = f.read().strip()

    try:
        recent_bill = get_most_recent_reported_bill()

        if recent_bill and recent_bill["bill_id"] != last_bill_id:
            # Construct the tweet text
            tweet_text = f"New bill introduced: {recent_bill['title']} ({recent_bill['bill_id']})\\n{recent_bill['summary']}"

            # Tweet about the new bill
            last_tweet_id = tweet_thread(api, tweet_text)

            # If the tweet was successfully posted, update the last tweeted bill ID
            if last_tweet_id:
                with open(LAST_BILL_FILE, "w") as f:
                    f.write(recent_bill["bill_id"])
        
        logging.info(f"Most recent reported bill: {recent_bill}")

    except tweepy.TweepError as e:
        logging.error(f"Failed to tweet: {e}", exc_info=True)
    except Exception as e:
        logging.error(f"Failed to fetch or tweet about the new bill: {e}", exc_info=True)

if __name__ == "__main__":
    main()
