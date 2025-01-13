from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from ytmusicapi import YTMusic
from ytmusicapi.auth.oauth import OAuthCredentials
import asyncio
import json
import os
import time

load_dotenv()

BRAND = os.getenv("BRAND")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
PORT = os.getenv("PORT") or 6969
OAUTH = os.getenv("OAUTH")

if OAUTH is None:
    raise Exception("OAUTH must be provided")
else:
    with open("oauth.json", "w") as f:
        f.write(OAUTH)

if CLIENT_ID is None or CLIENT_SECRET is None:
    raise Exception("CLIENT_ID and CLIENT_SECRET must be provided")

oauth_credentials=OAuthCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
ytmusic = YTMusic("oauth.json", BRAND, oauth_credentials=oauth_credentials)

listening_to = None

async def run_background():
    global listening_to
    while True:
        await asyncio.sleep(5)
        try:
            history = ytmusic.get_history()
            last_song = ytmusic.get_playlist(playlistId="FEmusic_history", limit=1)
            print("Last song:", last_song)
        except Exception as e:
            print("Error:", e)
            continue
        
        song = history[0]
        if listening_to is None or listening_to["title"] != song["title"]:
            listening_to = {
                "title": song["title"],
                "artist": song["artists"][0]["name"],
                "thumbnail": song["thumbnails"][0]["url"],
                "duration_s": song["duration_seconds"],
                "started": time.time(),
                "url": f"https://music.youtube.com/watch?v={song['videoId']}"
            }

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(run_background())
    yield
        
app = FastAPI(lifespan=lifespan)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return "Youtube Music live listening API"


@app.get("/live")
async def live():
    # create generator that yields data when new song is played
    async def streamer_live():
        while True:
            yield f"data: {json.dumps(listening_to)}\n\n"
            await asyncio.sleep(5)

    return StreamingResponse(streamer_live())


@app.get("/last")
async def last():
    return json.dumps(listening_to)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6969, limit_max_requests=100)