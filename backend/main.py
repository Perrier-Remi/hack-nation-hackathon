from fastapi import FastAPI

app = FastAPI(title="Hack Nation Hackathon API", version="1.0.0")

@app.post("/video-analysis")
async def video_analysis(video_url: str):
    return {"message": "Video analysis started"}