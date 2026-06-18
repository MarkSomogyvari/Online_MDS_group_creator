import os
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, Optional, List
import random
import math
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
    return templates.TemplateResponse(request=request, name="index.html")

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

def calculate_pure_python_mds(distance_matrix, n_components=2, lr=0.05, iterations=500):
    n = len(distance_matrix)
    random.seed(42)
    X = [[random.uniform(-1, 1) for _ in range(n_components)] for _ in range(n)]
    
    for _ in range(iterations):
        gradients = [[0.0] * n_components for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                diff = [X[i][d] - X[j][d] for d in range(n_components)]
                dist = math.sqrt(sum(d**2 for d in diff))
                if dist < 1e-5:
                    dist = 1e-5
                
                target_dist = distance_matrix[i][j]
                factor = 2.0 * (dist - target_dist) / dist
                for d in range(n_components):
                    gradients[i][d] += factor * diff[d]
                    
        for i in range(n):
            for d in range(n_components):
                X[i][d] -= lr * gradients[i][d]
                
    mean_x = sum(pt[0] for pt in X) / n
    mean_y = sum(pt[1] for pt in X) / n
    for i in range(n):
        X[i][0] -= mean_x
        X[i][1] -= mean_y
        
    return X

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
        
        distance_matrix = [[3.0] * n for _ in range(n)]
        
        scores = conn.execute("SELECT rater_id, rated_id, score FROM scores").fetchall()
        for s in scores:
            i = participant_ids.index(s["rater_id"])
            j = participant_ids.index(s["rated_id"])
            distance_matrix[i][j] = 6 - s["score"]
        
        for i in range(n):
            for j in range(n):
                if i < j:
                    avg = (distance_matrix[i][j] + distance_matrix[j][i]) / 2
                    distance_matrix[i][j] = avg
                    distance_matrix[j][i] = avg
        
        for i in range(n):
            distance_matrix[i][i] = 0.0
        
        coordinates = calculate_pure_python_mds(distance_matrix)
        
        result = []
        for idx, p in enumerate(participants):
            result.append({
                "name": p["name"],
                "x": float(coordinates[idx][0]),
                "y": float(coordinates[idx][1])
            })
        
        return result

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse(request=request, name="admin.html")

@app.get("/admin/participants-details", response_class=JSONResponse)
async def get_participants_details(x_admin_password: Optional[str] = Header(None)):
    if x_admin_password != "alma":
        raise HTTPException(status_code=401, detail="Unauthorized")
    with get_db() as conn:
        participants = conn.execute("SELECT id, name, created_at FROM participants").fetchall()
        scores = conn.execute("SELECT rater_id, rated_id, score FROM scores").fetchall()
        
        scores_dict = {}
        for s in scores:
            scores_dict.setdefault(s["rater_id"], {})[s["rated_id"]] = s["score"]
            
        result = []
        for p in participants:
            result.append({
                "id": p["id"],
                "name": p["name"],
                "created_at": p["created_at"],
                "scores": scores_dict.get(p["id"], {})
            })
        return result

@app.post("/admin/reset", response_class=JSONResponse)
async def reset_db(x_admin_password: Optional[str] = Header(None)):
    if x_admin_password != "alma":
        raise HTTPException(status_code=401, detail="Unauthorized")
    with get_db() as conn:
        conn.execute("DELETE FROM scores")
        conn.execute("DELETE FROM participants")
        conn.commit()
        return {"status": "success"}

@app.post("/admin/mock", response_class=JSONResponse)
async def load_mock_data(x_admin_password: Optional[str] = Header(None)):
    if x_admin_password != "alma":
        raise HTTPException(status_code=401, detail="Unauthorized")
    with get_db() as conn:
        # Clear existing
        conn.execute("DELETE FROM scores")
        conn.execute("DELETE FROM participants")
        
        # Add participants
        names = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"]
        ids = []
        for name in names:
            cursor = conn.execute("INSERT INTO participants (name) VALUES (?)", (name,))
            ids.append(cursor.lastrowid)
        
        # Pairwise scores setup
        mock_scores = {
            0: {1: 5, 2: 4, 3: 1, 4: 2, 5: 1}, # Alice
            1: {0: 5, 2: 5, 3: 2, 4: 1, 5: 2}, # Bob
            2: {0: 4, 1: 5, 3: 2, 4: 2, 5: 1}, # Charlie
            3: {0: 1, 1: 2, 2: 1, 4: 5, 5: 4}, # David
            4: {0: 2, 1: 1, 2: 2, 3: 5, 5: 5}, # Eve
            5: {0: 1, 1: 2, 2: 1, 3: 4, 4: 5}, # Frank
        }
        
        for r_idx, ratings in mock_scores.items():
            rater_id = ids[r_idx]
            for rated_idx, score in ratings.items():
                rated_id = ids[rated_idx]
                conn.execute(
                    "INSERT OR REPLACE INTO scores (rater_id, rated_id, score) VALUES (?, ?, ?)",
                    (rater_id, rated_id, score)
                )
        conn.commit()
        return {"status": "success"}

@app.delete("/admin/participants/{p_id}", response_class=JSONResponse)
async def delete_participant(p_id: int, x_admin_password: Optional[str] = Header(None)):
    if x_admin_password != "alma":
        raise HTTPException(status_code=401, detail="Unauthorized")
    with get_db() as conn:
        conn.execute("DELETE FROM scores WHERE rater_id = ? OR rated_id = ?", (p_id, p_id))
        conn.execute("DELETE FROM participants WHERE id = ?", (p_id,))
        conn.commit()
        return {"status": "success"}
