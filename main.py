from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from ytmusicapi import YTMusic
from ytmusicapi.auth.oauth import OAuthCredentials
import os, time, json, asyncio

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

RELOAD_TIME = 5

oauth_credentials=OAuthCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
ytmusic = YTMusic("oauth.json", BRAND, oauth_credentials=oauth_credentials)

listening_to = None
last_song_name = None
last_update = time.time()
connections = []

async def update_history():
    global listening_to, last_update, last_song_name
    
    current_time = time.time()
    if current_time - last_update < RELOAD_TIME: 
        return
    last_update = current_time
    
    try:
        history = ytmusic.get_history()
    except Exception as e:
        print("Error:", e)
        return
    
    song = history[0] # TODO: figure out a cheaper way to get the most recent song listened to

    if last_song_name != song["title"]:
        last_song_name = song["title"]
        listening_to = {
            "title": song["title"],
            "artist": song["artists"][0]["name"],
            "thumbnail": song["thumbnails"][0]["url"],
            "duration_s": song["duration_seconds"],
            "started": current_time - (RELOAD_TIME / 2 + 1), # artificially display the song starting a bit earlier because of interval delay
            "url": f"https://music.youtube.com/watch?v={song['videoId']}"
        }
    elif listening_to and listening_to["started"] + listening_to["duration_s"] < current_time:
        listening_to = None
        
        
async def run_background():
    while True:
        await update_history()
        await asyncio.sleep(RELOAD_TIME)
        
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
    async def streamer_live():
        while True:
            yield f"data: {json.dumps(listening_to, default=str)}\n\n"
            await asyncio.sleep(RELOAD_TIME)

    return StreamingResponse(streamer_live(), media_type="text/event-stream")

@app.get("/last")
async def last():
    await update_history()
    return json.dumps(listening_to)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6969, limit_max_requests=100)