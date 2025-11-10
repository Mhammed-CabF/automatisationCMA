# Utilise l'image Playwright officielle (Chromium déjà inclus)
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# Crée un répertoire pour ton app
WORKDIR /app

# Copie les fichiers de ton projet
COPY . /app

# Installe les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Expose le port utilisé par Uvicorn
EXPOSE 10000

# Lance ton app FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
