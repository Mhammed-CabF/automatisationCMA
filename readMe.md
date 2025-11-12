python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn playwright
python -m playwright install chromium

#lancer l'api locallement
uvicorn main:app --reload@

#lancer ngrock
ngrok http 8000