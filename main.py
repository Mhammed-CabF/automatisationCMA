import asyncio
import sys
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

CMA_URL = "https://www.exament3p.fr"


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

            if debug:
                print("[STEP] Attente affichage formulaire popup")

            await page.wait_for_selector("#modalFirstName", timeout=15000)

            # --------- REMPLISSAGE FORMULAIRE ---------
            if debug:
                print("[STEP] Remplissage champs")

            await page.fill("#modalFirstName", data.get("prenom", ""))
            await page.fill("#modalLastName", data.get("nom", ""))
            await page.fill("#modalBirthDate", data.get("date_naissance", ""))  # YYYY-MM-DD valid
            await page.fill("#modalBirthPlace", data.get("lieu_naissance", ""))
            await page.fill("#modalBirthCountry", data.get("pays_naissance", ""))  # Auto-complete OK
            await page.fill("#modalAddress", data.get("adresse", ""))
            await page.fill("#modalPostalCode", data.get("code_post", ""))
            await page.fill("#modalCity", data.get("ville", ""))
            await page.fill("#modalEmail", data.get("email", ""))
            await page.fill("#modalPhone", data.get("phone", ""))
            await page.fill("#modalPassword", data.get("password", ""))
            await page.fill("#modalPasswordConfirm", data.get("password", ""))

            # --------- CASES OBLIGATOIRES ---------
            if debug:
                print("[STEP] Cases à cocher")

            await page.check("#modalConnexionExamRules")
            await page.check("#modalConnexionProfessionConditions")

            # RGPD case must be checked by clicking label (checkbox has readonly)
            await page.click("label[for='modalConnexionRGPD']")


            # --------- SOUMISSION ---------
            if debug:
                print("[STEP] Envoi formulaire")

            await page.click("button.saveAccountCreation")

            # Attendre soit réussite, soit message d’erreur
            await page.wait_for_timeout(3000)

            # Vérifier un message de validation visible
            success_msg = await page.query_selector("text=compte créé") or \
                          await page.query_selector("text=Votre compte a bien été créé")

            if success_msg:
                if debug:
                    print("[✅ SUCCESS] Compte créé avec succès")
                await browser.close()
                return {"status": "success", "deal_id": deal_id}

            # Sinon → erreur visible
            await page.screenshot(path=screenshot_path, full_page=True)
            if debug:
                print(f"Aucun message de succès. Screenshot enregistré : {screenshot_path}")
                print("Le navigateur reste ouvert pour inspection.")
                return {"status": "error", "deal_id": deal_id, "screenshot": screenshot_path}

            await browser.close()
            return {"status": "error", "deal_id": deal_id, "screenshot": screenshot_path}

        except Exception as e:
            await page.screenshot(path=screenshot_path, full_page=True)
            if debug:
                print(f"{e}, screenshot: {screenshot_path}")
                print("Le navigateur reste ouvert pour inspection.")
            else:
                await browser.close()
            return {"status": "exception", "deal_id": deal_id, "error": str(e), "screenshot": screenshot_path}


# ---------------- CLI MODE ----------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python playwright_cma.py payload.json [--debug]")
        sys.exit(1)

    payload_file = Path(sys.argv[1])
    debug_mode = "--debug" in sys.argv

    if not payload_file.exists():
        print(f"payload introuvable: {payload_file}")
        sys.exit(1)

    data = json.loads(payload_file.read_text())

    print("▶️ Test en cours...")
    result = asyncio.run(create_cma_account(data, debug=debug_mode))
    print("✅ Résultat Playwright :", result)
