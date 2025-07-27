# AI-Powered Candidate Filtering System

This project is an AI-powered system to efficiently filter job candidates from a large pool of applicants.

## Architecture

The system is built on a serverless architecture using Azure services to ensure scalability, maintainability, and cost-effectiveness.

- **Frontend**: React SPA (Vite + Tailwind CSS) deployed on Azure Static Web Apps.
- **Backend**: Python-based Azure Functions.
- **Database**: SQLite on Azure Files.
- **Storage**: Azure Blob Storage for resumes (PDFs and images).
- **AI Model**: Azure ML Online Endpoint hosting a VLM.
- **Data Retrieval**: Scheduled Playwright script to download resumes.

Refer to the architecture diagram for a visual overview.

## Project Structure

- `frontend/`: Contains the React frontend application.
- `backend/`: Contains the Azure Functions backend.
  - `api/`: Main API functions.
  - `resume_processor/`: Function for processing resumes.
- `data_retriever/`: Script for automated resume retrieval.
- `config/`: Environment-specific configurations.
- `database/`: Local SQLite database.
- `local_storage/`: Local directory for storing resume PDFs and images. 