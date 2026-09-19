# ⚡ Smart Task Manager

A production-grade, collaborative full-stack task and project management web application built with **Django 5+**, **Django REST Framework (DRF)**, **Bootstrap 5**, **PostgreSQL**, **Redis**, and **Celery**.

Designed for engineering and product teams to plan sprints, track deliverables on an interactive drag-and-drop **Kanban board**, filter workloads across multiple dimensions, monitor velocity through a real-time **analytics dashboard**, and automate 24-hour deadline email notifications.

---

## 🌟 Key Features

- **Robust Authentication & Roles**: Django authentication with secure session management, registration, profile customization (avatar, job title, department, bio), and notification preferences.
- **Projects & Permissions**: Multi-tenant workspace model with granular access controls (`Owner`, `Project Admin`, `Member`, `Viewer`). Only project members can view or modify tasks.
- **Task Organization**: Create, edit, assign, prioritize (`Low`, `Medium`, `High`, `Urgent`), and tag tasks with customized color badges.
- **Interactive Drag & Drop Kanban**: Fluid HTML5 drag-and-drop board across 4 states (`To Do`, `In Progress`, `In Review`, `Done`) with instant AJAX persistence, count badges, and mobile button fallbacks.
- **Comprehensive Search & Multi-Filters**: Filter tasks by project, status, priority, tag, assignee, and overdue status, alongside full-text search.
- **Executive Analytics Dashboard**: Metric cards (Total Tasks, Completion Rate %, Overdue count), Chart.js visualizations (status doughnut and priority breakdown), upcoming 7-day deadlines table, and team activity timeline.
- **Celery & Redis 24h Deadline Alerts**: Asynchronous worker and Celery Beat scheduler checking upcoming task deadlines (< 24h) and dispatching personalized reminder emails.
- **RESTful API**: Complete Django REST Framework API endpoints for projects, tasks, tags, user profiles, and aggregated dashboard analytics.
- **Audit Logging**: Automated task history tracking documenting status changes, reassignments, and timestamps.
- **Dual Database Flexibility**: Native PostgreSQL for Docker & production, with automatic SQLite fallback for instant local development.
- **Docker Compose**: Production-minded multi-container setup (Django Web, PostgreSQL 16, Redis 7, Celery Worker, Celery Beat).

---


## 📸 Application Previews

### Executive Analytics Dashboard
![Executive Analytics Dashboard](docs/screenshots/dashboard.jpg)

### Interactive Drag & Drop Kanban Board
![Kanban Board](docs/screenshots/kanban.jpg)

### Task Directory & Advanced Multi-Filters
![Task Directory](docs/screenshots/tasks_directory.jpg)

## 🏗️ Architecture Overview

```text
                               +----------------------------------------+
                               |              Web Browser               |
                               |    (Bootstrap 5 + Chart.js + AJAX)     |
                               +-------------------+--------------------+
                                                   |
                                                   v
                               +----------------------------------------+
                               |          Django 5 Application          |
                               |  - Accounts & RBAC Permissions         |
                               |  - Projects & Task Workflows           |
                               |  - DRF REST API Endpoints              |
                               +---------+-------------------+----------+
                                         |                   |
                     +-------------------+                   +-------------------+
                     |                                                           |
                     v                                                           v
+--------------------+--------------------+                     +----------------+--------------------+
|             PostgreSQL 16               |                     |               Redis 7               |
|      (or SQLite for local dev)          |                     |     (Celery Broker & Result Store)  |
+-----------------------------------------+                     +----------------+--------------------+
                                                                                 |
                                                                                 v
                                                                +----------------+--------------------+
                                                                |         Celery Worker & Beat        |
                                                                | - Periodic hourly deadline checks   |
                                                                | - Automated notification dispatch   |
                                                                +-------------------------------------+
```

---

## 📁 Project Structure

```text
smart-task-manager/
├── config/                  # Django project root configuration
│   ├── settings.py          # Environment-driven settings & logging
│   ├── urls.py              # Root URL routing & error handlers
│   ├── celery.py            # Celery app & beat schedule configuration
│   ├── wsgi.py / asgi.py    # Deployment entrypoints
│   └── __init__.py          # Celery initialization
├── apps/
│   ├── accounts/            # User profile extension, registration & auth
│   ├── projects/            # Project models, memberships & role permissions
│   ├── tasks/               # Tasks, tags, activity audit, Celery task & seed
│   ├── dashboard/           # Aggregated statistics & Chart.js endpoints
│   └── api/                 # Django REST Framework serializers & viewsets
├── templates/
│   ├── base.html            # Core layout, navbar & sidebar navigation
│   ├── includes/            # Partials (navbar, sidebar, messages, pagination)
│   ├── accounts/            # Login, register, profile
│   ├── projects/            # Project list, detail, form, delete
│   ├── tasks/               # Task list, kanban board, detail, form, delete
│   ├── dashboard/           # Main analytics dashboard
│   └── errors/              # 403, 404, 500 error pages
├── static/
│   ├── css/style.css        # Custom styles, priority badges & Kanban styles
│   └── js/                  # main.js (CSRF, toasts) & kanban.js (Drag & drop)
├── tests/                   # Automated unit and integration tests
├── requirements/            # Split requirements (base, local, production)
├── Dockerfile               # Multi-stage container definition
├── docker-compose.yml       # Web, PostgreSQL, Redis, Celery worker & beat
├── entrypoint.sh            # Database readiness check & migration runner
├── manage.py                # Django CLI tool
├── .env.example             # Template environment variables
└── README.md
```

---

## 🚀 Quick Start with Docker (Recommended)

### 1. Clone & Configure Environment
```bash
cp .env.example .env
```

### 2. Build & Launch Containers
Run all 5 services (`web`, `db`, `redis`, `celery_worker`, `celery_beat`) in the background:
```bash
docker compose up --build -d
```

### 3. Populate Demo Seed Data
```bash
docker compose exec web python manage.py seed_data
```

### 4. Access the Application
- **Web App**: [http://localhost:8000](http://localhost:8000)
- **REST API**: [http://localhost:8000/api/v1/](http://localhost:8000/api/v1/)
- **Django Admin**: [http://localhost:8000/admin/](http://localhost:8000/admin/)

---

## 💻 Local Development (Without Docker / SQLite)

If you do not have Docker installed or prefer running lightweight local development with **SQLite**:

### 1. Create Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements/local.txt
```

### 3. Initialize Database & Seed Demo Data
```bash
# Migrates schema into local db.sqlite3
python manage.py migrate

# Seeds realistic demo users, projects, tags, and tasks
python manage.py seed_data
```

### 4. Start Development Server
```bash
python manage.py runserver
```
Visit [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

---

## 👥 Demo Accounts

The seed script creates ready-to-test accounts across different roles:

| Username | Password | Full Name | Role | Access Level |
| :--- | :--- | :--- | :--- | :--- |
| **`admin`** | `AdminPass123!` | Sarah Connor | Engineering Director | Superuser, Full Django Admin access |
| **`alice_pm`** | `DemoPass123!` | Alice Vance | Principal Product Manager | Project Admin & Member |
| **`bob_dev`** | `DemoPass123!` | Bob Stone | Senior Full-Stack Engineer | Project Member (Can edit tasks) |
| **`charlie_designer`** | `DemoPass123!` | Charlie Reed | Lead UX/UI Designer | Project Viewer / Member |

> **Tip**: The login page includes **one-click demo login buttons** to instantly pre-fill credentials for quick portfolio reviews!

---

## ⚙️ Environment Variables

| Variable | Default | Description |
| :--- | :--- | :--- |
| `SECRET_KEY` | `django-insecure-...` | Django secret key (set a secure random string in production) |
| `DEBUG` | `True` | Toggle Django debug mode |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1,web` | Comma-separated allowed hostnames |
| `DATABASE_URL` | *(empty = SQLite)* | PostgreSQL connection URL e.g. `postgres://user:pass@host:5432/dbname` |
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | Redis broker URL for Celery |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/0` | Redis result backend for Celery |
| `CELERY_TASK_ALWAYS_EAGER` | `False` | Run Celery tasks synchronously (useful for test runs) |
| `EMAIL_BACKEND` | `...console.EmailBackend` | Django email backend (`console` for dev, `smtp` for prod) |
| `DEFAULT_FROM_EMAIL` | `noreply@smarttaskmanager.local` | Outgoing sender address |

---

## ⏰ Celery & Automated Deadline Reminders

The background task `apps.tasks.tasks.send_task_deadline_reminders` runs periodically via **Celery Beat**:
1. Queries tasks due within the next 24 hours (`now <= due_date <= now + 24h`) where status is not `done`.
2. Verifies whether the assignee has `email_notifications` enabled in their profile.
3. Dispatches a formatted notification email with task title, due date, priority, and project link.
4. Sets `reminder_sent_at` on the task so duplicate emails are never sent.

### Running Celery Manually in Local Dev:
In two separate terminal tabs (with `.venv` activated and Redis running):
```bash
# Terminal 1: Celery Worker
celery -A config worker --loglevel=info

# Terminal 2: Celery Beat Scheduler
celery -A config beat --loglevel=info
```

To test the reminder task logic instantly in the Django shell:
```bash
python manage.py shell -c "from apps.tasks.tasks import send_task_deadline_reminders; print(send_task_deadline_reminders())"
```

---

## 🔌 REST API Endpoints

The API is mounted at `/api/v1/` and requires Session or Basic Authentication:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/dashboard/stats/` | Real-time workspace metrics, completion rate, priority distribution |
| `GET`, `PUT` | `/api/v1/auth/profile/` | Current authenticated user's profile and notification settings |
| `GET`, `POST` | `/api/v1/projects/` | List user projects or create a new project |
| `GET`, `PUT`, `DELETE` | `/api/v1/projects/<id>/` | Project details, updates, or deletion (admin/owner only) |
| `POST` | `/api/v1/projects/<id>/toggle_archive/` | Archive or unarchive a project |
| `GET`, `POST` | `/api/v1/tasks/` | List accessible tasks (supports `?project=`, `?status=`, `?priority=`, `?tag=`, `?overdue=1`) |
| `GET`, `PUT`, `DELETE` | `/api/v1/tasks/<id>/` | Retrieve, edit, or delete a task |
| `POST` | `/api/v1/tasks/<id>/update-status/` | Kanban endpoint to update status (`{"status": "in_progress"}`) |
| `GET`, `POST` | `/api/v1/tags/` | List or create tags with hex color codes |

---

## 🧪 Testing Suite

Run the full automated test suite (unit and integration tests for authentication, permissions, task CRUD, Kanban drag-and-drop, Celery reminders, and DRF endpoints):

```bash
# Using Django test runner
python manage.py test tests/ --verbosity=2

# Or using pytest
pytest
```

---

## 🔒 Security Practices

- **Role-Based Access Control (RBAC)**: All project queries and task modifications enforce project membership. Non-members receive strict HTTP 403 Forbidden responses.
- **CSRF Protection**: All form submissions and AJAX calls (including drag-and-drop movements) require valid CSRF tokens.
- **Secure Password Hashing**: Utilizes Django's PBKDF2 with SHA-256 password hashing.
- **Unprivileged Docker Container**: The Docker image creates and runs under an unprivileged `appuser` (UID 1000).
- **Environment Isolation**: Secrets, database credentials, and debug flags are loaded strictly from environment variables.

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
