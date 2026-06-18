import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, Optional
import numpy as np
import pandas as pd
from sklearn.manifold import MDS
import sqlite3
import json
from contextlib import contextmanager

app = FastAPI(title="Workshop Group Finder")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DB_PATH = "workshop.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rater_id INTEGER NOT NULL,
                rated_id INTEGER NOT NULL,
                score INTEGER NOT NULL,
                FOREIGN KEY (rater_id) REFERENCES participants(id),
                FOREIGN KEY (rated_id) REFERENCES participants(id),
                UNIQUE(rater_id, rated_id)
            )
        """)
        conn.commit()

class Participant(BaseModel):
    name: str

class ScoreInput(BaseModel):
    scores: Dict[int, int]

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/participants", response_class=JSONResponse)
async def get_participants():
    with get_db() as conn:
        participants = conn.execute("SELECT id, name FROM participants").fetchall()
        return [{"id": p["id"], "name": p["name"]} for p in participants]

@app.post("/participants", response_class=JSONResponse)
async def register_participant(participant: Participant):
    with get_db() as conn:
        try:
            result = conn.execute(
                "INSERT INTO participants (name) VALUES (?)",
                (participant.name,)
            )
            conn.commit()
            return {"id": result.lastrowid, "name": participant.name}
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Participant already exists")

@app.get("/scores", response_class=JSONResponse)
async def get_scores(rater_id: int):
    with get_db() as conn:
        scores = conn.execute(
            "SELECT rated_id, score FROM scores WHERE rater_id = ?",
            (rater_id,)
        ).fetchall()
        return {str(s["rated_id"]): s["score"] for s in scores}

@app.post("/scores", response_class=JSONResponse)
async def submit_scores(score_input: ScoreInput, rater_id: int):
    with get_db() as conn:
        for rated_id_str, score in score_input.scores.items():
            if score is None:
                score = 3
            conn.execute(
                """INSERT OR REPLACE INTO scores (rater_id, rated_id, score) VALUES (?, ?, ?)""",
                (rater_id, int(rated_id_str), score)
            )
        conn.commit()
        return {"status": "success"}

@app.get("/mds", response_class=JSONResponse)
async def calculate_mds():
    with get_db() as conn:
        participants = conn.execute("SELECT id, name FROM participants").fetchall()
        
        if len(participants) < 1:
            raise HTTPException(status_code=400, detail="No participants found")
        
        participant_ids = [p["id"] for p in participants]
        n = len(participant_ids)
        
        if n == 1:
            raise HTTPException(status_code=400, detail="Need at least 2 participants for MDS")
        
        distance_matrix = np.full((n, n), 3.0)
        
        scores = conn.execute("SELECT rater_id, rated_id, score FROM scores").fetchall()
        for s in scores:
            i = participant_ids.index(s["rater_id"])
            j = participant_ids.index(s["rated_id"])
            distance_matrix[i, j] = 6 - s["score"]
        
        for i in range(n):
            for j in range(n):
                if i < j:
                    avg = (distance_matrix[i, j] + distance_matrix[j, i]) / 2
                    distance_matrix[i, j] = avg
                    distance_matrix[j, i] = avg
        
        np.fill_diagonal(distance_matrix, 0)
        
        mds = MDS(n_components=2, dissimilarity='precomputed', random_state=42)
        coordinates = mds.fit_transform(distance_matrix)
        
        result = []
        for idx, p in enumerate(participants):
            result.append({
                "name": p["name"],
                "x": float(coordinates[idx, 0]),
                "y": float(coordinates[idx, 1])
            })
        
        return result
