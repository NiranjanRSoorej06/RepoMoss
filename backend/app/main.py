from __future__ import annotations
import json, uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel, Field
from .services import core

app=FastAPI(title="RepoMoss",version="0.1.0",description="Local-first repository maintenance assistant")
app.add_middleware(CORSMiddleware,allow_origins=["http://127.0.0.1:8000","http://localhost:8000"],allow_methods=["GET","POST"],allow_headers=["Content-Type"])

class Register(BaseModel): path:str
class RunRequest(BaseModel): verification_commands:list[str]=Field(default_factory=list)

def fail(fn,*args):
    try:return fn(*args)
    except Exception as e: raise HTTPException(400,str(e))
def dump(row): return dict(row) if row else None

@app.get("/api/health")
def health():
    import shutil, urllib.request
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags",timeout=1) as r: ollama=r.status==200
    except Exception: ollama=False
    return {"status":"ok","git":bool(shutil.which("git")),"ollama":ollama,"database":str(core.DB_PATH)}

@app.post("/api/repositories")
def register(body:Register):
    meta=fail(core.repo_meta,body.path); c=core.db(); existing=c.execute("SELECT * FROM repositories WHERE path=?",(meta["path"],)).fetchone()
    if existing: rid=existing["id"]; c.execute("UPDATE repositories SET branch=?,commit_id=? WHERE id=?",(meta["branch"],meta["commit"],rid))
    else:
        rid=str(uuid.uuid4()); c.execute("INSERT INTO repositories VALUES(?,?,?,?,?,?)",(rid,meta["path"],meta["name"],meta["branch"],meta["commit"],core.now()))
    c.commit(); c.close(); return {"id":rid,**meta}

@app.get("/api/repositories")
def repositories():
    c=core.db(); rows=[dict(x) for x in c.execute("SELECT * FROM repositories ORDER BY created_at DESC")]; c.close(); return rows

@app.get("/api/repositories/{repo_id}")
def repository(repo_id:str):
    c=core.db(); row=c.execute("SELECT * FROM repositories WHERE id=?",(repo_id,)).fetchone(); c.close()
    if not row: raise HTTPException(404,"Repository not found")
    return dict(row)

@app.post("/api/repositories/{repo_id}/scan")
def scan(repo_id:str):
    c=core.db(); repo=c.execute("SELECT * FROM repositories WHERE id=?",(repo_id,)).fetchone(); c.close()
    if not repo: raise HTTPException(404,"Repository not found")
    data=dict(repo); data["commit"]=data["commit_id"]
    return fail(core.scan,data)

@app.get("/api/repositories/{repo_id}/tasks")
def tasks(repo_id:str):
    c=core.db(); rows=c.execute("SELECT t.id,t.finding_id,t.plan_json,t.policy_status,t.review_status,t.created_at,f.category,f.title,f.description,f.file_paths_json,f.evidence_json,f.priority,f.risk,f.status FROM tasks t JOIN findings f ON f.id=t.finding_id JOIN scans s ON s.id=f.scan_id WHERE s.repository_id=? ORDER BY f.priority DESC",(repo_id,)).fetchall(); c.close()
    return [{**dict(x),"plan":json.loads(x["plan_json"]),"files":json.loads(x["file_paths_json"]),"evidence":json.loads(x["evidence_json"])} for x in rows]

@app.post("/api/tasks/{task_id}/{action}")
def task_action(task_id:str,action:str):
    if action not in {"approve","defer","reject"}: raise HTTPException(404,"Unknown task action")
    status={"approve":"approved","defer":"deferred","reject":"rejected"}[action]; c=core.db(); cur=c.execute("UPDATE tasks SET review_status=? WHERE id=?",(status,task_id)); c.commit(); c.close()
    if not cur.rowcount: raise HTTPException(404,"Task not found")
    return {"id":task_id,"review_status":status}

@app.post("/api/tasks/{task_id}/plan")
def plan(task_id:str):
    c=core.db(); row=c.execute("SELECT t.id,f.title,f.description,f.file_paths_json,f.evidence_json,f.risk FROM tasks t JOIN findings f ON f.id=t.finding_id WHERE t.id=?",(task_id,)).fetchone()
    if not row: c.close(); raise HTTPException(404,"Task not found")
    finding={"title":row["title"],"description":row["description"],"files":json.loads(row["file_paths_json"]),"evidence":json.loads(row["evidence_json"]),"risk":row["risk"]}
    data=core.plan_with_ollama(finding); c.execute("UPDATE tasks SET plan_json=? WHERE id=?",(json.dumps(data),task_id)); c.commit(); c.close(); return data

@app.post("/api/tasks/{task_id}/run")
def run(task_id:str,body:RunRequest): return fail(core.attempt,task_id,body.verification_commands)

@app.get("/api/runs/{run_id}")
def get_run(run_id:str):
    c=core.db(); row=c.execute("SELECT * FROM runs WHERE id=?",(run_id,)).fetchone(); checks=[dict(x) for x in c.execute("SELECT * FROM verification_results WHERE run_id=?",(run_id,))]; events=[dict(x) for x in c.execute("SELECT * FROM run_events WHERE run_id=? ORDER BY id",(run_id,))]; c.close()
    if not row: raise HTTPException(404,"Run not found")
    return {**dict(row),"verification":checks,"events":events}

@app.get("/api/runs/{run_id}/diff",response_class=PlainTextResponse)
def get_diff(run_id:str):
    c=core.db(); found=c.execute("SELECT 1 FROM runs WHERE id=?",(run_id,)).fetchone(); c.close()
    if not found: raise HTTPException(404,"Run not found")
    p=core.LOG_DIR/f"{run_id}.diff"; return p.read_text() if p.exists() else ""

@app.get("/api/runs/{run_id}/report",response_class=PlainTextResponse)
def get_report(run_id:str): return fail(core.report,run_id)

@app.get("/api/runs/{run_id}/events")
def get_events(run_id:str): return get_run(run_id)["events"]

@app.post("/api/runs/{run_id}/cancel")
def cancel(run_id:str): raise HTTPException(409,"Runs execute synchronously; cancellation is not available in this MVP")

@app.get("/",response_class=HTMLResponse)
def ui(): return (Path(__file__).parents[2]/"frontend"/"index.html").read_text()
