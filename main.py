from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from ytmusicapi import YTMusic
import asyncio
import json
import os
import time

load_dotenv()

brand = os.getenv("BRAND")
ytmusic = YTMusic("oauth.json", brand)

listening_to = None

async def run_background():
    global listening_to
    while True:
        history = ytmusic.get_history()
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
        await asyncio.sleep(5)

app = FastAPI()

origins = [
    "*"
]

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



@app.on_event('startup')
async def app_startup():
    asyncio.create_task(run_background())
