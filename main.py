from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from datetime import timedelta
from typing import List
import uuid
from datetime import datetime
from pydantic import BaseModel
import logging

from models import User, UserCreate, Project, ProjectCreate, Task, TaskCreate, Token
from auth import (
    get_current_active_user,
    create_access_token,
    get_password_hash,
    verify_password,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from storage import JSONStorage

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Teamly API")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все источники
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все методы
    allow_headers=["*"],  # Разрешаем все заголовки
)

storage = JSONStorage()

class LoginRequest(BaseModel):
    username: str
    password: str

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
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "hashed_password": hashed_password,
    }
    storage.save_user(user_dict)
    return User(**{k: v for k, v in user_dict.items() if k != "hashed_password"})

@app.post("/token", response_model=Token)
async def login(login_data: LoginRequest):
    logger.info(f"Login attempt for user: {login_data.username}")
    
    users = storage.get_users()
    logger.info(f"Total users in storage: {len(users)}")
    
    user = next((u for u in users if u["email"] == login_data.username), None)
    if not user:
        logger.warning(f"User not found: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"User found: {user['email']}")
    password_verified = verify_password(login_data.password, user["hashed_password"])
    logger.info(f"Password verification result: {password_verified}")
    
    if not password_verified:
        logger.warning(f"Invalid password for user: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    logger.info(f"Token generated for user: {login_data.username}")
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

@app.put("/projects/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_active_user)
):
    # Получаем проект
    projects = storage.get_projects()
    project = next((p for p in projects if p["id"] == project_id), None)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    # Проверяем, является ли пользователь владельцем проекта
    if project["owner_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can edit the project",
        )
    
    # Обновляем данные проекта
    updated_project = {
        **project,
        "name": project_data.name,
        "description": project_data.description,
    }
    
    storage.update_project(project_id, updated_project)
    return Project(**updated_project)

@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(
    task_id: str,
    task_data: TaskCreate,
    current_user: User = Depends(get_current_active_user)
):
    # Получаем задачу
    tasks = storage.get_tasks()
    task = next((t for t in tasks if t["id"] == task_id), None)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    
    # Проверяем доступ к проекту
    projects = storage.get_projects()
    project = next((p for p in projects if p["id"] == task["project_id"]), None)
    if not project or current_user.id not in project["members"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    # Обновляем данные задачи
    updated_task = {
        **task,
        "title": task_data.title,
        "description": task_data.description,
    }
    
    storage.update_task(task_id, updated_task)
    return Task(**updated_task)
