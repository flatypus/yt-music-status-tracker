
from dotenv import load_dotenv
from ytmusicapi import YTMusic
from ytmusicapi.auth.oauth import OAuthCredentials
import os

load_dotenv()

BRAND = os.getenv("BRAND")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

if CLIENT_ID is None or CLIENT_SECRET is None:
    raise Exception("CLIENT_ID and CLIENT_SECRET must be provided")

print("BRAND:", BRAND)
print("CLIENT_ID:", CLIENT_ID)
print("CLIENT_SECRET:", CLIENT_SECRET)

oauth_credentials=OAuthCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
ytmusic = YTMusic("oauth.json", oauth_credentials=oauth_credentials)

# history = ytmusic.get_history()
# print(history)