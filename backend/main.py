from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
from typing import Optional
from models import TasksResponse, StatsResponse
from analyzer import analyze_tasks

app = FastAPI(title="Task Analytics API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # при деплое заменить на URL фронтенда
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "message": "Task Analytics API"}


@app.post("/api/upload", response_model=TasksResponse)
async def upload_file(file: UploadFile = File(...)):
    """Принимает .xlsx или .csv, возвращает список задач + статистику."""
    if not file.filename.endswith((".xlsx", ".csv")):
        raise HTTPException(400, "Поддерживаются только .xlsx и .csv файлы")

    content = await file.read()

    try:
        if file.filename.endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(content))
        else:
            df = pd.read_csv(io.StringIO(content.decode("utf-8")))
    except Exception as e:
        raise HTTPException(422, f"Не удалось прочитать файл: {e}")

    return analyze_tasks(df)


@app.get("/api/health")
def health():
    return {"status": "healthy"}
