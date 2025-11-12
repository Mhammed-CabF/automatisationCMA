import asyncio
import json
from pathlib import Path
from fastapi import FastAPI, Request
from playwright.async_api import async_playwright
from fastapi import BackgroundTasks

CMA_URL = "https://www.exament3p.fr"

app = FastAPI()

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

            await page.goto(CMA_URL, wait_until="networkidle", timeout=30000)

            # --- Connexion / Ouverture formulaire
            await page.get_by_role("link", name="Se connecter").click()
            await page.wait_for_url("**/id/14", timeout=15000)
            await page.get_by_role("button", name="Créér").click()
            await page.wait_for_selector("#modalFirstName", timeout=15000)

            # --- Genre
            civilite = data.get("genre", "").strip().lower()
            if "madame" in civilite:
                await page.check("#gender_F")
            else:
                await page.check("#gender_M")

            # --- Champs texte
            await page.fill("#modalFirstName", data.get("prenom", ""))
            await page.fill("#modalLastName", data.get("nom", ""))
            await page.fill("#modalBirthDate", data.get("date_naissance", ""))
            await page.fill("#modalBirthPlace", data.get("lieu_naissance", ""))
            await page.fill("#modalBirthCountry", data.get("pays_naissance", ""))
            await page.fill("#modalAddress", data.get("adresse", ""))
            await page.fill("#modalPostalCode", data.get("code_post", ""))
            await page.fill("#modalCity", data.get("ville", ""))
            await page.fill("input[name='uac_email']", data.get("email", ""))
            await page.fill("input[name='secondary_email']", data.get("secondary_email", ""))
            await page.fill("#modalPhone", data.get("phone", ""))
            await page.fill("#modalPassword", data.get("password", ""))
            await page.fill("#modalPasswordConfirm", data.get("password", ""))

            # --- Cases à cocher
            await page.check("#modalConnexionExamRules")
            await page.check("#modalConnexionProfessionConditions")
            await page.click("label[for='modalConnexionRGPD']")

            # --- Envoi formulaire
            await page.click("button.saveAccountCreation")
            await page.wait_for_timeout(4000)

            # --- Vérifications de résultat
            content = await page.content()

            # ✅ Cas 1 : message de succès
            if "Votre compte a bien été créé" in content or "compte créé" in content:
                if debug:
                    print("[✅ SUCCESS] Compte créé avec succès")
                await browser.close()
                return {"status": "success", "deal_id": deal_id}

            # ⚠️ Cas 2 : erreurs visibles (ex: mail déjà utilisé)
            error_messages = await page.query_selector_all(".error, .text-danger, .alert-danger")
            if error_messages:
                errors_text = []
                for el in error_messages:
                    txt = (await el.inner_text()).strip()
                    if txt:
                        errors_text.append(txt)
                await page.screenshot(path=screenshot_path, full_page=True)
                await browser.close()
                return {
                    "status": "form_error",
                    "deal_id": deal_id,
                    "errors": errors_text,
                    "screenshot": screenshot_path
                }

            # ❓ Cas 3 : aucun message clair
            await page.screenshot(path=screenshot_path, full_page=True)
            await browser.close()
            return {
                "status": "unknown",
                "deal_id": deal_id,
                "message": "Aucun message de succès ni d'erreur détecté",
                "screenshot": screenshot_path
            }

        except Exception as e:
            await page.screenshot(path=screenshot_path, full_page=True)
            if debug:
                print(f"[💥 EXCEPTION] {e}")
            await browser.close()
            return {
                "status": "exception",
                "deal_id": deal_id,
                "error": str(e),
                "screenshot": screenshot_path
            }

# ------------------ ROUTES FASTAPI ------------------

@app.get("/")
def root():
    return {"message": "✅ CMA automation API is running on Render"}


@app.post("/zoho/webhook")
async def webhook(request: Request):
    data = await request.json()
    print("📦 Données reçues :", data)

    async def safe_task():
        try:
            result = await create_cma_account(data, debug=True)
            print(f"[RESULT] {data.get('deal_id')}: {result['status']}")
            if result.get("errors"):
                print("🧩 Détails erreurs :", result["errors"])
        except Exception as e:
            print("💥 Erreur Playwright :", e)

    asyncio.create_task(safe_task())

    return {"status": "queued", "message": "Automatisation CMA en cours"}

