import asyncio
from playwright.async_api import async_playwright, Page
from browser_use import Agent, BrowserSession
from browser_use.llm import ChatOpenAI
from dotenv import load_dotenv
import os
import requests
import json
import logging
from omegaconf import OmegaConf

# --- Setup ---
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv("../.env")

CONFIG_PATH = os.getenv("CONFIG_PATH", "../config/retriever_config.yaml")
config = OmegaConf.load(CONFIG_PATH)

# --- Configuration ---
PORTAL_URL = config.prod.portal_url
DOWNLOAD_DIR = config.prod.download_dir
API_ENDPOINT = config.prod.api_endpoint
USER_DATA_DIR = config.prod.user_data_dir
OPENAI_API_KEY = config.prod.openai_api_key

if not USER_DATA_DIR or not OPENAI_API_KEY:
    raise ValueError("USER_DATA_DIR and OPENAI_API_KEY environment variables must be set.")

# --- browser-use Agent Task ---
AGENT_TASK = """
Your goal is to extract candidate information from the job portal.
1. You should already be on the main job application page.
2. Identify the table or list containing the candidates.
3. For each candidate, extract the following fields: 'Role', 'Candidate', 'Candidate type', 'Apply date', 'Status', 'Last update', 'CV' (this will be a download link), and 'Cover Letter' (also a download link).
4. Return the data as a JSON object, where each key is the candidate's name and the value is an object with the extracted fields. The 'CV' and 'Cover Letter' fields should contain the full URL to the downloadable files.
"""

class LoginError(Exception):
    """Custom exception for login failures."""
    pass

def log_login_failure_and_exit():
    """Logs detailed instructions for the user on how to refresh cookies."""
    logging.error("AUTOMATED LOGIN FAILED: The script could not access the portal.")
    instructions = """
    This is likely because your browser session has expired. To fix this, please refresh your authentication cookies:
    
    1. Manually open the Microsoft Edge browser on your machine.
    2. Navigate to the internal portal: {}
    3. Log in with your corporate credentials. If you are already logged in, log out and log back in.
    4. Ensure you check any "Keep me logged in" or "Remember me" option if available.
    5. Close the browser completely.
    6. Re-run this script.

    This process updates your session cookies, allowing the script to authenticate on your behalf.
    """.format(PORTAL_URL)
    logging.info(instructions)
    raise LoginError("Exiting due to login failure.")


async def download_and_upload_file(page: Page, url: str, job_title: str, candidate_name: str, file_type: str):
    """Downloads a file from a given URL and uploads it to the backend."""
    if not url:
        logging.info(f"No {file_type} URL for {candidate_name}")
        return

    try:
        # Navigate to the URL to trigger download
        async with page.expect_download() as download_info:
            await page.goto(url)
        
        download = await download_info.value
        filename = download.suggested_filename
        download_path = os.path.join(DOWNLOAD_DIR, filename)
        await download.save_as(download_path)
        logging.info(f"Downloaded '{filename}'")

        await upload_file_to_backend(download_path, job_title, candidate_name)
    except Exception as e:
        logging.error(f"Failed to download or upload {file_type} for {candidate_name}: {e}")


async def upload_file_to_backend(file_path, job_title, candidate_name):
    """Uploads a file to the backend API."""
    if not os.path.exists(file_path):
        logging.info(f"File not found: {file_path}")
        return

    logging.info(f"Uploading '{os.path.basename(file_path)}' for candidate '{candidate_name}'...")
    
    with open(file_path, 'rb') as f:
        files = {'resume': (os.path.basename(file_path), f, 'application/pdf')}
        data = {'job_title': job_title, 'candidate_name': candidate_name}
        
        try:
            response = requests.post(API_ENDPOINT, files=files, data=data)
            response.raise_for_status()
            logging.info(f"Upload successful for {os.path.basename(file_path)}.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to upload {os.path.basename(file_path)}: {e}")
        finally:
            os.remove(file_path)


async def main():
    """
    Uses Playwright to establish an authenticated session with MS Edge, then hands
    over control to a browser-use agent to extract data.
    """
    async with async_playwright() as p:
        logging.info("Launching Microsoft Edge with persistent context...")
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=True,
            accept_downloads=True,
            channel="msedge",  # Use the Edge browser
        )
        cdp_url = browser.browser.ws_endpoint
        page = await browser.new_page()

        try:
            logging.info(f"Navigating to portal: {PORTAL_URL}")
            await page.goto(PORTAL_URL, wait_until='domcontentloaded')

            # --- Login Verification ---
            # Check if we were redirected to a common login page.
            if "login" in page.url or "signin" in page.url or "auth" in page.url:
                log_login_failure_and_exit()

            # Connect browser-use to the existing authenticated browser session
            browser_session = BrowserSession(cdp_url=cdp_url)
            llm = ChatOpenAI(model="gpt-4o")
            agent = Agent(task=AGENT_TASK, llm=llm, browser_session=browser_session)
            
            logging.info("Running browser-use agent to extract candidate data...")
            result = await agent.run()
            
            if not result:
                logging.warning("Agent did not return any data. This could indicate a login failure or no new candidates.")
                # You might still be logged in, but the agent found nothing.
                # Check for content that should be present when logged in.
                logout_button = await page.query_selector('button:has-text("Logout")')
                if not logout_button:
                    log_login_failure_and_exit()
                return

            candidate_data = json.loads(result)
            logging.info(f"Agent extracted data for {len(candidate_data)} candidates.")

            # Use the authenticated Playwright page to download files
            download_page = await browser.new_page()
            for candidate_name, details in candidate_data.items():
                logging.info(f"--- Processing candidate: {candidate_name} ---")
                job_title = details.get('Role')

                await download_and_upload_file(download_page, details.get('CV'), job_title, candidate_name, 'CV')
                await download_and_upload_file(download_page, details.get('Cover Letter'), job_title, candidate_name, 'Cover Letter')

        except LoginError:
            # The login failure has already been logged. Just exit.
            return
        except Exception as e:
            logging.error(f"An unexpected error occurred during the process: {e}")
            # Check if the error might be due to a disconnected browser (another sign of login/auth issues)
            if not browser.is_connected():
                 log_login_failure_and_exit()
        finally:
            logging.info("Closing browser session.")
            await browser.close()


if __name__ == "__main__":
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
    
    # Run main and suppress the LoginError from bubbling up to the console
    try:
        asyncio.run(main())
    except LoginError:
        pass