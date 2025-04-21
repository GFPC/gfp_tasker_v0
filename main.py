from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import List
import uuid
from datetime import datetime

from models import User, UserCreate, Project, ProjectCreate, Task, TaskCreate, Token
from auth import (
    get_current_active_user,
    create_access_token,
    get_password_hash,
    verify_password,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from storage import JSONStorage

app = FastAPI(title="Teamly API")
storage = JSONStorage()

@app.post("/register", response_model=User)
async def register(user: UserCreate):
    users = storage.get_users()
    if any(u["email"] == user.email for u in users):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    hashed_password = get_password_hash(user.password)
    user_dict = {
        "id": str(uuid.uuid4()),
        "email": user.email,
        "name": user.name,
        "created_at": datetime.utcnow(),
        "hashed_password": hashed_password,
    }
    storage.save_user(user_dict)
    return User(**{k: v for k, v in user_dict.items() if k != "hashed_password"})

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    users = storage.get_users()
    user = next((u for u in users if u["email"] == form_data.username), None)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@app.post("/projects", response_model=Project)
async def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_active_user)
):
    project_dict = {
        "id": str(uuid.uuid4()),
        "name": project.name,
        "description": project.description,
        "owner_id": current_user.id,
        "created_at": datetime.utcnow(),
        "members": [current_user.id],
    }
    storage.save_project(project_dict)
    return Project(**project_dict)

@app.get("/projects", response_model=List[Project])
async def get_projects(current_user: User = Depends(get_current_active_user)):
    projects = storage.get_projects()
    return [Project(**p) for p in projects if current_user.id in p["members"]]

@app.post("/tasks", response_model=Task)
async def create_task(
    task: TaskCreate,
    current_user: User = Depends(get_current_active_user)
):
    # Verify project exists and user has access
    projects = storage.get_projects()
    project = next((p for p in projects if p["id"] == task.project_id), None)
    if not project or current_user.id not in project["members"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied",
        )
    
    task_dict = {
        "id": str(uuid.uuid4()),
        "title": task.title,
        "description": task.description,
        "project_id": task.project_id,
        "created_at": datetime.utcnow(),
        "status": "todo",
    }
    storage.save_task(task_dict)
    return Task(**task_dict)

@app.get("/tasks", response_model=List[Task])
async def get_tasks(current_user: User = Depends(get_current_active_user)):
    projects = storage.get_projects()
    user_projects = [p["id"] for p in projects if current_user.id in p["members"]]
    tasks = storage.get_tasks()
    return [Task(**t) for t in tasks if t["project_id"] in user_projects]

@app.put("/tasks/{task_id}/assign")
async def assign_task(
    task_id: str,
    assignee_id: str,
    current_user: User = Depends(get_current_active_user)
):
    tasks = storage.get_tasks()
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    
    # Verify project access
    projects = storage.get_projects()
    project = next((p for p in projects if p["id"] == task["project_id"]), None)
    if not project or current_user.id not in project["members"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    # Verify assignee is a project member
    if assignee_id not in project["members"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignee must be a project member",
        )
    
    task["assignee_id"] = assignee_id
    storage.update_task(task_id, task)
    return Task(**task)

@app.put("/tasks/{task_id}/status")
async def update_task_status(
    task_id: str,
    status: str,
    current_user: User = Depends(get_current_active_user)
):
    tasks = storage.get_tasks()
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    
    # Verify project access
    projects = storage.get_projects()
    project = next((p for p in projects if p["id"] == task["project_id"]), None)
    if not project or current_user.id not in project["members"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    valid_statuses = ["todo", "in_progress", "done"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Status must be one of {valid_statuses}",
        )
    
    task["status"] = status
    storage.update_task(task_id, task)
    return Task(**task)
