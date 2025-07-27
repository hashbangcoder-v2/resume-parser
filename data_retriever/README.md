# Data Retriever

This script automates the retrieval of new candidate resumes from an internal job portal using **Microsoft Edge**.

## How It Works

It uses [Playwright](https://playwright.dev/) to launch a headless Microsoft Edge browser instance. To handle authentication for Single Sign-On (SSO), it leverages a persistent browser context, which means it can use the cookies from your existing, logged-in Edge session.

Once an authenticated session is established, it hands over control to a [browser-use](https://github.com/browser-use/browser-use) agent powered by GPT-4o. The agent intelligently navigates the portal, extracts candidate data from the page, and returns it as structured JSON.

The script will:
1.  Launch a headless **Edge** browser using a specified user data directory.
2.  Navigate to the internal job portal URL and verify that the login was successful.
3.  If login fails, it will provide detailed instructions on how to refresh your browser cookies.
4.  Run the `browser-use` agent to extract candidate details and download links.
5.  Download the CV and Cover Letter for each candidate.
6.  Upload the downloaded files to the application's backend.

## ⚠️ Important Setup

This script requires manual configuration to work with your specific environment.

### 1. Environment Variables

Create a `.env` file in this directory or set the following environment variables:

-   `PORTAL_URL`: The URL of your internal job portal.
-   `USER_DATA_DIR`: **(Required)** The absolute path to your **Microsoft Edge** user data directory. This is essential for SSO to work.
    -   **Windows:** `%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default`
    -   **macOS (Apple Silicon):** `~/Library/Application Support/Microsoft Edge/Default`
    -   **macOS (Intel):** `~/Library/Application Support/Microsoft Edge/Default`
    -   **Linux:** `~/.config/microsoft-edge/Default`
-   `OPENAI_API_KEY`: Your API key for the GPT-4o model.
-   `API_ENDPOINT`: The URL of the backend API's upload endpoint (defaults to local).
-   `DOWNLOAD_DIR`: The directory to temporarily store downloaded resumes.

### 2. Portal-Specific Logic

While `browser-use` is robust, its effectiveness can be improved by refining the `AGENT_TASK` prompt in `retriever.py`. If you find the agent is failing, consider making the prompt more specific to your portal's layout.

## Usage

1.  **Install dependencies:**
    ```bash
    # Navigate to the backend directory
    cd ../backend
    # Activate your virtual environment
    source .venv/bin/activate 
    # Install/update packages
    uv pip install -r requirements.txt
    ```

2.  **Install Playwright browsers:**
    ```bash
    playwright install msedge
    ```

3.  **Run the script:**
    ```bash
    python retriever.py
    ```

This script is designed to be run on a schedule (e.g., daily) using a tool like `cron`, GitHub Actions, or a time-triggered Azure Function. 