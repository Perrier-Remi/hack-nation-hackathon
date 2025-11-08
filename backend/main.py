from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pipeline.video_pipeline import VideoPipeline
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Créer le dossier uploads s'il n'existe pas
os.makedirs("uploads", exist_ok=True)

@app.post("/analyze-video")
async def upload_video(video: UploadFile = File(...)):
    # Sauvegarder le fichier
    video_path = f"uploads/{video.filename}"
    with open(video_path, "wb") as buffer:
        content = await video.read()
        buffer.write(content)
    
    video_pipeline = VideoPipeline(video_path)
    result = video_pipeline.run()
    
    return result

