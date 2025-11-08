from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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

@app.post("/upload-video")
async def upload_video(video: UploadFile = File(...)):
    # Sauvegarder le fichier
    with open(f"uploads/{video.filename}", "wb") as buffer:
        content = await video.read()
        buffer.write(content)
    
    return {
        "filename": video.filename,
        "content_type": video.content_type,
        "size": len(content)
    }

