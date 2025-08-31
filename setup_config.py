"""
Configuration constants and file templates for AIS setup system.
"""

# AIS Version
AIS_VERSION = "3.2.1"

# Directory structure to create
DIRECTORIES = [
    "ais",
    "ais/core",
    "ais/api",
    "ais/api/routes",
    "ais/utils",
    "ais/data_manager",
    "config",
    "docker",
    "docker/nginx",
    "kubernetes",
    "src",
    "src/api",
    "src/services",
    "src/stores",
    "src/hooks",
    "src/components",
    "src/pages",
    "checkpoints",
    "tests"
]

# File templates with initial content
FILE_TEMPLATES = {
    "ais/__init__.py": '"""AIS Core Package"""',
    "ais/core/__init__.py": '"""AIS Core Components"""',
    "ais/api/__init__.py": '"""AIS API Package"""',
    "ais/api/routes/__init__.py": '"""AIS API Routes"""',
    "ais/utils/__init__.py": '"""AIS Utilities"""',
    "ais/data_manager/__init__.py": '"""AIS Data Manager"""',
    "config/__init__.py": '"""Configuration Package"""',
    "tests/__init__.py": '"""Test Package"""',
    "config/settings.py": '''"""
AIS Configuration Settings
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

# API Configuration
API_HOST = os.getenv("AIS_HOST", "0.0.0.0")
API_PORT = int(os.getenv("AIS_PORT", "8000"))
API_DEBUG = os.getenv("AIS_DEBUG", "false").lower() == "true"

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///ais.db")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "ais.log")

# Security Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

# Model Configuration
MODEL_PATH = BASE_DIR / "checkpoints"
MAX_MODEL_SIZE = int(os.getenv("MAX_MODEL_SIZE", "1000000000"))  # 1GB

# Performance Configuration
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))
TIMEOUT = int(os.getenv("TIMEOUT", "30"))
''',
    "docker/Dockerfile": '''FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "app.py"]
''',
    "docker/nginx/nginx.conf": '''events {
    worker_connections 1024;
}

http {
    upstream ais_backend {
        server app:8000;
    }

    server {
        listen 80;
        
        location / {
            proxy_pass http://ais_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
''',
    "kubernetes/deployment.yaml": '''apiVersion: apps/v1
kind: Deployment
metadata:
  name: ais-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ais
  template:
    metadata:
      labels:
        app: ais
    spec:
      containers:
      - name: ais
        image: ais:latest
        ports:
        - containerPort: 8000
        env:
        - name: AIS_HOST
          value: "0.0.0.0"
        - name: AIS_PORT
          value: "8000"
---
apiVersion: v1
kind: Service
metadata:
  name: ais-service
spec:
  selector:
    app: ais
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
''',
    ".gitignore": '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
*.log
logs/

# Database
*.db
*.sqlite3

# Models
checkpoints/*.pth
checkpoints/*.pkl

# OS
.DS_Store
Thumbs.db

# AIS specific
setup_ais.log
'''
}

# Logging configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "filename": "setup_ais.log"
}

# Default configuration values
DEFAULT_CONFIG = {
    "cleanup_existing": True,
    "install_dependencies": True,
    "create_files": True,
    "verbose": False
}