import json
import os
from typing import Dict, List, Any
from pathlib import Path

class JSONStorage:
    def __init__(self, storage_dir: str = "data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.users_file = self.storage_dir / "users.json"
        self.projects_file = self.storage_dir / "projects.json"
        self.tasks_file = self.storage_dir / "tasks.json"
        
        # Initialize files if they don't exist
        for file in [self.users_file, self.projects_file, self.tasks_file]:
            if not file.exists():
                with open(file, "w") as f:
                    json.dump([], f)
    
    def _read_file(self, file_path: Path) -> List[Dict]:
        with open(file_path, "r") as f:
            return json.load(f)
    
    def _write_file(self, file_path: Path, data: List[Dict]):
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def get_users(self) -> List[Dict]:
        return self._read_file(self.users_file)
    
    def get_projects(self) -> List[Dict]:
        return self._read_file(self.projects_file)
    
    def get_tasks(self) -> List[Dict]:
        return self._read_file(self.tasks_file)
    
    def save_user(self, user: Dict):
        users = self.get_users()
        users.append(user)
        self._write_file(self.users_file, users)
    
    def save_project(self, project: Dict):
        projects = self.get_projects()
        projects.append(project)
        self._write_file(self.projects_file, projects)
    
    def save_task(self, task: Dict):
        tasks = self.get_tasks()
        tasks.append(task)
        self._write_file(self.tasks_file, tasks)
    
    def update_user(self, user_id: str, user_data: Dict):
        users = self.get_users()
        for i, user in enumerate(users):
            if user["id"] == user_id:
                users[i] = {**user, **user_data}
                break
        self._write_file(self.users_file, users)
    
    def update_project(self, project_id: str, project_data: Dict):
        projects = self.get_projects()
        for i, project in enumerate(projects):
            if project["id"] == project_id:
                projects[i] = {**project, **project_data}
                break
        self._write_file(self.projects_file, projects)
    
    def update_task(self, task_id: str, task_data: Dict):
        tasks = self.get_tasks()
        for i, task in enumerate(tasks):
            if task["id"] == task_id:
                tasks[i] = {**task, **task_data}
                break
        self._write_file(self.tasks_file, tasks) 