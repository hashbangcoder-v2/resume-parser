# Needle-in-a-Haystack 

When you are reviewing hundreds of resumes each month, you wish you had a way to only review the good ones! This is a project borne out of that experience. Normally, one would use an API key from OpenAI or Google to handle the actual parsing and evaluation. But given data confidentiality of files involved, we need to use local open-models!

### TODO
- [x] Skeletal functionality to upload resumes and evaluate them for a job
- [x] Local deployment of backend, frontend and database
- [x] Get end-end functioanlity with one VLM model (Qwen2.5-Omni-7B)
- [x] Support multiple/hybridVLM models for user to choose from (Gemma3, GLM-4.1, Mix of reasoning models + lightweight Doc parsing models)
  - [ ] Implement hot-swap with vllm 
- [ ] RL fine-tune (mix of RLHF + RLVR) VLM models to learn from preferences
    - [ ] generate synthetic data for fine-tune


## Architecture

- **Frontend**: A modern React single-page application built with Next.js and styled with Tailwind CSS. 
- **Backend**: A robust API built with Python and FastAPI. It handles business logic, data processing, and communication with the database and AI models.
- **Database**: Uses SQLite. Making it easy to get started. If needed, it can be configured to use any database supported by SQLAlchemy.
- **Storage**: Supports both local file storage and Azure Blob Storage for data stores
- **AI Model**: Integrates with a Vision Language Model (VLM) for intelligent resume analysis. The model can be run locally or accessed via an ML Online Endpoint.

## Project Structure

- `frontend/`: Contains the React frontend application.
- `backend/`: Contains the FastAPI backend application.
- `config/`: Holds environment-specific configurations for the backend.
- `database/`: Contains the local SQLite database file.

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js**: Required for the frontend.
- **Python / FastAPI**: Required for the backend.
- **Poppler**: A system-level dependency for processing PDF files.
- **uv**: A modern Python package manager 

**Installing Poppler:**
- **On Debian/Ubuntu:**
  ```bash
  sudo apt-get update && sudo apt-get install -y poppler-utils
  ```
- **On Windows:**
  Follow the instructions in the [pdf2image documentation](https://pypi.org/project/pdf2image/) to install Poppler for Windows.

### Backend Setup

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2.  **Create and activate a virtual environment and install all dependencies:**
    ```bash
    uv venv
    uv sync
    ```

3.  **Set the `PROJECT_ROOT` environment or modify the .env file**
    This variable is required for the backend to locate configuration and database files.

4.  **Seed the database:**
    If you want to start with some sample data for local dev/testing:
    ```bash
    uv run seed_db
    ```

### Frontend Setup

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```

2.  **Create a `.env.local` file:**
    This file stores the environment variables for the frontend.
    ```
    NEXT_PUBLIC_API_BASE_URL="http://127.0.0.1:8000"
    ```

3.  **Install the required Node.js packages:**
    ```bash
    npm install
    ```

### Running the Application

1.  **Start the backend server:**
    From the `backend` directory, run:
    ```bash
    wfc-serve
    ```
    The API will be available at `http://localhost:8000`.

2.  **Start the frontend development server:**
    From the `frontend` directory, run:
    ```bash
    npm run dev
    ```
    Open [http://localhost:3000](http://localhost:3000) in your browser to see the application.

### Test Data
Tests use sample files from `test-files/`:
- `sample_resume_1.pdf` - Valid resume sample #1
- `sample_resume_2.pdf` - Valid resume sample #2
- `sample_false.pdf` - Invalid resume for error testing

### Expected Results
- **LLM Tests**: Structured JSON responses with name, email, outcome, and reasoning
- **Route Tests**: Proper HTTP status codes and response formats
- **Integration Tests**: Complete workflows from job creation to application review
- **Error Cases**: Consistent error handling (404, 422, 400 status codes)
