import asyncio
import json
from pathlib import Path
from fastapi import FastAPI, Request
from playwright.async_api import async_playwright
from fastapi import BackgroundTasks

CMA_URL = "https://www.exament3p.fr"

app = FastAPI()

# ------------------ TA FONCTION EXISTANTE ------------------
async def create_cma_account(data: dict, debug: bool = False) -> dict:
    deal_id = data.get("deal_id", "unknown")
    screenshot_path = f"screenshot_{deal_id}.png"
    launch_args = {"headless": not debug, "args": ["--no-sandbox"]}

    async with async_playwright() as p:
        browser = await p.chromium.launch(**launch_args)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            if debug:
                print("[STEP] Ouverture site CMA")

            await page.goto(CMA_URL, wait_until="networkidle")

            if debug:
                print("[STEP] Click Se connecter")

            await page.get_by_role("link", name="Se connecter").click()
            await page.wait_for_url("**/id/14", timeout=15000)

            if debug:
                print("[STEP] Click bouton Créér")

            await page.get_by_role("button", name="Créér").click()
            await page.wait_for_selector("#modalFirstName", timeout=15000)

            if debug:
                print("[STEP] Remplissage champs")

            await page.fill("#modalFirstName", data.get("prenom", ""))
            await page.fill("#modalLastName", data.get("nom", ""))
            await page.fill("#modalBirthDate", data.get("date_naissance", ""))
            await page.fill("#modalBirthPlace", data.get("lieu_naissance", ""))
            await page.fill("#modalBirthCountry", data.get("pays_naissance", ""))
            await page.fill("#modalAddress", data.get("adresse", ""))
            await page.fill("#modalPostalCode", data.get("code_post", ""))
            await page.fill("#modalCity", data.get("ville", ""))
            await page.fill("#modalEmail", data.get("email", ""))
            await page.fill("#modalPhone", data.get("phone", ""))
            await page.fill("#modalPassword", data.get("password", ""))
            await page.fill("#modalPasswordConfirm", data.get("password", ""))

            if debug:
                print("[STEP] Cases à cocher")

            await page.check("#modalConnexionExamRules")
            await page.check("#modalConnexionProfessionConditions")
            await page.click("label[for='modalConnexionRGPD']")

            if debug:
                print("[STEP] Envoi formulaire")

            await page.click("button.saveAccountCreation")
            await page.wait_for_timeout(3000)

            success_msg = await page.query_selector("text=compte créé") or \
                          await page.query_selector("text=Votre compte a bien été créé")

            if success_msg:
                if debug:
                    print("[✅ SUCCESS] Compte créé avec succès")
                await browser.close()
                return {"status": "success", "deal_id": deal_id}

            await page.screenshot(path=screenshot_path, full_page=True)
            if debug:
                print(f"Aucun message de succès. Screenshot enregistré : {screenshot_path}")
            await browser.close()
            return {"status": "error", "deal_id": deal_id, "screenshot": screenshot_path}

        except Exception as e:
            await page.screenshot(path=screenshot_path, full_page=True)
            if debug:
                print(f"{e}, screenshot: {screenshot_path}")
            await browser.close()
            return {"status": "exception", "deal_id": deal_id, "error": str(e), "screenshot": screenshot_path}


# ------------------ ROUTES FASTAPI ------------------

@app.get("/")
def root():
    return {"message": "✅ CMA automation API is running on Render"}


#@app.post("/zoho/webhook")
#async def webhook(request: Request):
#    """Reçoit les données du workflow Zoho CRM"""
#    data = await request.json()
#    print("📦 Données reçues :", data)
 #   result = await create_cma_account(data, debug=False)
 #   return result

@app.post("/zoho/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    print("📦 Données reçues :", data)

    # Lancer Playwright en arrière-plan
    background_tasks.add_task(create_cma_account, data, False)

    # Répondre tout de suite à Zoho
    return {"status": "queued", "message": "Automatisation CMA en cours"}