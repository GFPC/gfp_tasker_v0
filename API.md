# API Documentation

## Аутентификация

Все запросы к API (кроме регистрации и входа) требуют JWT токена в заголовке:
```
Authorization: Bearer <your_token>
```

## Endpoints

### Регистрация

**POST /register**

Регистрация нового пользователя.

Request body:
```json
{
    "email": "user@example.com",
    "name": "John Doe",
    "password": "password123"
}
```

Response (200):
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "name": "John Doe",
    "created_at": "2024-01-01T12:00:00"
}
```

### Вход

**POST /token**

Получение JWT токена для доступа к API.

Request body:
```json
{
    "username": "user@example.com",
    "password": "password123"
}
```

Response (200):
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
}
```

### Пользователь

**GET /users/me**

Получение информации о текущем пользователе.

Response (200):
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "name": "John Doe",
    "created_at": "2024-01-01T12:00:00"
}
```

### Проекты

**POST /projects**

Создание нового проекта.

Request body:
```json
{
    "name": "My Project",
    "description": "Project description"
}
```

Response (200):
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "My Project",
    "description": "Project description",
    "owner_id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2024-01-01T12:00:00",
    "members": ["550e8400-e29b-41d4-a716-446655440000"]
}
```

**GET /projects**

Получение списка проектов пользователя.

Response (200):
```json
[
    {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "name": "My Project",
        "description": "Project description",
        "owner_id": "550e8400-e29b-41d4-a716-446655440000",
        "created_at": "2024-01-01T12:00:00",
        "members": ["550e8400-e29b-41d4-a716-446655440000"]
    }
]
```

**GET /projects/{project_id}**

Получение данных конкретного проекта. Доступно только для участников проекта.

Response (200):
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "My Project",
    "description": "Project description",
    "owner_id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2024-01-01T12:00:00",
    "members": ["550e8400-e29b-41d4-a716-446655440000"]
}
```

Возможные ошибки:
- `404 Not Found` - Проект не найден
- `403 Forbidden` - Пользователь не является участником проекта

**PUT /projects/{project_id}**

Редактирование проекта. Только владелец проекта может его редактировать.

Request body:
```json
{
    "name": "Updated Project Name",
    "description": "Updated project description"
}
```

Response (200):
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "Updated Project Name",
    "description": "Updated project description",
    "owner_id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2024-01-01T12:00:00",
    "members": ["550e8400-e29b-41d4-a716-446655440000"]
}
```

Возможные ошибки:
- `404 Not Found` - Проект не найден
- `403 Forbidden` - Пользователь не является владельцем проекта

### Задачи

**POST /tasks**

Создание новой задачи.

Request body:
```json
{
    "title": "Task title",
    "description": "Task description",
    "project_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

Response (200):
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "title": "Task title",
    "description": "Task description",
    "project_id": "550e8400-e29b-41d4-a716-446655440001",
    "created_at": "2024-01-01T12:00:00",
    "status": "todo",
    "assignee_id": null
}
```

**GET /tasks**

Получение списка задач пользователя.

Response (200):
```json
[
    {
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "title": "Task title",
        "description": "Task description",
        "project_id": "550e8400-e29b-41d4-a716-446655440001",
        "created_at": "2024-01-01T12:00:00",
        "status": "todo",
        "assignee_id": null
    }
]
```

**PUT /tasks/{task_id}/assign**

Назначение задачи пользователю.

Query parameters:
```
assignee_id: 550e8400-e29b-41d4-a716-446655440000
```

Response (200):
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "title": "Task title",
    "description": "Task description",
    "project_id": "550e8400-e29b-41d4-a716-446655440001",
    "created_at": "2024-01-01T12:00:00",
    "status": "todo",
    "assignee_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**PUT /tasks/{task_id}/status**

Изменение статуса задачи.

Query parameters:
```
status: in_progress
```

Допустимые значения статуса:
- `todo`
- `in_progress`
- `done`

Response (200):
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "title": "Task title",
    "description": "Task description",
    "project_id": "550e8400-e29b-41d4-a716-446655440001",
    "created_at": "2024-01-01T12:00:00",
    "status": "in_progress",
    "assignee_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**PUT /tasks/{task_id}**

Редактирование задачи. Доступно для всех участников проекта.

Request body:
```json
{
    "title": "Updated Task Title",
    "description": "Updated task description",
    "project_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

Response (200):
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "title": "Updated Task Title",
    "description": "Updated task description",
    "project_id": "550e8400-e29b-41d4-a716-446655440001",
    "created_at": "2024-01-01T12:00:00",
    "status": "todo",
    "assignee_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

Возможные ошибки:
- `404 Not Found` - Задача не найдена
- `403 Forbidden` - Пользователь не имеет доступа к проекту

## Коды ошибок

- `400 Bad Request` - Неверный формат запроса
- `401 Unauthorized` - Неверные учетные данные или отсутствует токен
- `403 Forbidden` - Нет доступа к ресурсу
- `404 Not Found` - Ресурс не найден

## Примеры использования

### cURL

Регистрация:
```bash
curl -X POST "http://localhost:8000/register" \
     -H "Content-Type: application/json" \
     -d '{"email":"user@example.com","name":"John Doe","password":"password123"}'
```

Вход:
```bash
curl -X POST "http://localhost:8000/token" \
     -d "username=user@example.com&password=password123"
```

Создание проекта:
```bash
curl -X POST "http://localhost:8000/projects" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"name":"My Project","description":"Project description"}'
```

### Python

```python
import requests

# Регистрация
response = requests.post(
    "http://localhost:8000/register",
    json={
        "email": "user@example.com",
        "name": "John Doe",
        "password": "password123"
    }
)

# Вход
response = requests.post(
    "http://localhost:8000/token",
    data={
        "username": "user@example.com",
        "password": "password123"
    }
)
token = response.json()["access_token"]

# Создание проекта
response = requests.post(
    "http://localhost:8000/projects",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "name": "My Project",
        "description": "Project description"
    }
) 