import unittest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock, AsyncMock
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app import db_models as models, schemas
from app.db import get_db, Base
from app.config import get_config


class TestRoutes(unittest.TestCase):
    """Test suite for all FastAPI routes."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database and client."""
        # Create test database
        cls.SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
        cls.engine = create_engine(
            cls.SQLALCHEMY_DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=cls.engine
        )
        
        Base.metadata.create_all(bind=cls.engine)
        
        # Override database dependency
        def override_get_db():
            try:
                db = cls.TestingSessionLocal()
                yield db
            finally:
                db.close()
        
        # Mock config for testing
        cls.mock_config = {
            "app": {
                "env": "test",
                "host": "127.0.0.1",
                "port": 8000,
                "cors_origins": ["http://localhost:3000"]
            },
            "ai_model": {
                "endpoint": "http://localhost:8000/v1",
                "health_check_timeout_seconds": 5
            },
            "local_storage": {
                "path": "/tmp/test_resumes"
            },
            "vllm": {
                "inference_args": {
                    "limit_mm_per_prompt": {
                        "image": 3
                    }
                }
            }
        }
        
        def override_get_config():
            from omegaconf import OmegaConf
            return OmegaConf.create(cls.mock_config)
        
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_config] = override_get_config
        
        cls.client = TestClient(app)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test database."""
        Base.metadata.drop_all(bind=cls.engine)
        if os.path.exists("./test.db"):
            os.remove("./test.db")
    
    def setUp(self):
        """Set up each test with fresh database."""
        # Clear all tables
        db = self.TestingSessionLocal()
        try:
            db.query(models.Application).delete()
            db.query(models.Job).delete()
            db.query(models.Candidate).delete()
            db.commit()
        finally:
            db.close()
    
    def create_test_job(self, title="Software Engineer", description="Test job description"):
        """Helper to create a test job."""
        db = self.TestingSessionLocal()
        try:
            job = models.Job(title=title, description=description)
            db.add(job)
            db.commit()
            db.refresh(job)
            return job
        finally:
            db.close()
    
    def create_test_candidate(self, name="John Doe", email="john@example.com", resume_hash="test123"):
        """Helper to create a test candidate."""
        db = self.TestingSessionLocal()
        try:
            candidate = models.Candidate(name=name, email=email, resume_hash=resume_hash)
            db.add(candidate)
            db.commit()
            db.refresh(candidate)
            return candidate
        finally:
            db.close()
    
    def create_test_application(self, job_id, candidate_id, status="under_review", final_status="pending"):
        """Helper to create a test application."""
        db = self.TestingSessionLocal()
        try:
            application = models.Application(
                job_id=job_id,
                candidate_id=candidate_id,
                status=status,
                final_status=final_status,
                reason="Test reason"
            )
            db.add(application)
            db.commit()
            db.refresh(application)
            return application
        finally:
            db.close()


class TestJobsRoutes(TestRoutes):
    """Test suite for /api/jobs routes."""
    
    def test_create_job_success(self):
        """Test successful job creation."""
        job_data = {
            "title": "Senior Python Developer",
            "description": "Looking for an experienced Python developer"
        }
        
        response = self.client.post("/api/jobs", json=job_data)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["title"], job_data["title"])
        self.assertEqual(data["description"], job_data["description"])
        self.assertIn("id", data)
        self.assertIn("created_at", data)
    
    def test_create_job_duplicate_title(self):
        """Test job creation with duplicate title fails."""
        # Create first job
        self.create_test_job(title="Duplicate Job")
        
        # Try to create another with same title
        job_data = {
            "title": "Duplicate Job",
            "description": "This should fail"
        }
        
        response = self.client.post("/api/jobs", json=job_data)
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("already registered", response.json()["detail"])
    
    def test_create_job_missing_required_fields(self):
        """Test job creation with missing required fields."""
        job_data = {"description": "Missing title"}
        
        response = self.client.post("/api/jobs", json=job_data)
        
        self.assertEqual(response.status_code, 422)  # Validation error
    
    def test_get_all_jobs_empty(self):
        """Test getting all jobs when none exist."""
        response = self.client.get("/api/jobs")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
    
    def test_get_all_jobs_with_data(self):
        """Test getting all jobs with existing data."""
        # Create test jobs
        job1 = self.create_test_job("Job 1", "Description 1")
        job2 = self.create_test_job("Job 2", "Description 2")
        
        response = self.client.get("/api/jobs")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        
        titles = [job["title"] for job in data]
        self.assertIn("Job 1", titles)
        self.assertIn("Job 2", titles)
    
    def test_get_all_jobs_with_pagination(self):
        """Test getting jobs with pagination parameters."""
        # Create multiple jobs
        for i in range(5):
            self.create_test_job(f"Job {i}", f"Description {i}")
        
        # Test with limit
        response = self.client.get("/api/jobs?limit=2")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        
        # Test with skip
        response = self.client.get("/api/jobs?skip=2&limit=2")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
    
    def test_get_job_by_id_success(self):
        """Test getting a specific job by ID."""
        job = self.create_test_job("Test Job", "Test Description")
        
        response = self.client.get(f"/api/jobs/{job.id}")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], job.id)
        self.assertEqual(data["title"], "Test Job")
        self.assertEqual(data["description"], "Test Description")
    
    def test_get_job_by_id_not_found(self):
        """Test getting a non-existent job."""
        response = self.client.get("/api/jobs/999")
        
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.json()["detail"])
    
    def test_get_job_by_id_invalid_id(self):
        """Test getting a job with invalid ID format."""
        response = self.client.get("/api/jobs/invalid")
        
        self.assertEqual(response.status_code, 422)  # Validation error


class TestApplicationsRoutes(TestRoutes):
    """Test suite for /api/applications routes."""
    
    def test_update_application_status_success(self):
        """Test successful application status update."""
        # Create test data
        job = self.create_test_job()
        candidate = self.create_test_candidate()
        application = self.create_test_application(job.id, candidate.id)
        
        update_data = {"final_status": "accepted"}
        
        response = self.client.patch(f"/api/applications/{application.id}", json=update_data)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["final_status"], "accepted")
        self.assertEqual(data["id"], application.id)
    
    def test_update_application_status_not_found(self):
        """Test updating non-existent application."""
        update_data = {"final_status": "accepted"}
        
        response = self.client.patch("/api/applications/999", json=update_data)
        
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.json()["detail"])
    
    def test_update_application_status_invalid_data(self):
        """Test updating application with invalid data."""
        job = self.create_test_job()
        candidate = self.create_test_candidate()
        application = self.create_test_application(job.id, candidate.id)
        
        # Missing required field
        response = self.client.patch(f"/api/applications/{application.id}", json={})
        
        self.assertEqual(response.status_code, 422)  # Validation error
    
    def test_get_job_applications_success(self):
        """Test getting applications for a specific job."""
        # Create test data
        job = self.create_test_job()
        candidate1 = self.create_test_candidate("John Doe", "john@example.com", "hash1")
        candidate2 = self.create_test_candidate("Jane Smith", "jane@example.com", "hash2")
        
        app1 = self.create_test_application(job.id, candidate1.id, final_status="pending")
        app2 = self.create_test_application(job.id, candidate2.id, final_status="accepted")
        
        response = self.client.get(f"/api/applications/applications/{job.id}")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        
        # Verify application data
        app_ids = [app["id"] for app in data]
        self.assertIn(app1.id, app_ids)
        self.assertIn(app2.id, app_ids)
    
    def test_get_job_applications_empty(self):
        """Test getting applications for job with no applications."""
        job = self.create_test_job()
        
        response = self.client.get(f"/api/applications/applications/{job.id}")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
    
    def test_get_job_applications_with_pagination(self):
        """Test getting job applications with pagination."""
        job = self.create_test_job()
        
        # Create multiple applications
        for i in range(5):
            candidate = self.create_test_candidate(f"User {i}", f"user{i}@example.com", f"hash{i}")
            self.create_test_application(job.id, candidate.id)
        
        # Test with limit
        response = self.client.get(f"/api/applications/applications/{job.id}?limit=2")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        
        # Test with skip and limit
        response = self.client.get(f"/api/applications/applications/{job.id}?skip=2&limit=2")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)


class TestUploadRoutes(TestRoutes):
    """Test suite for /api/upload routes."""
    
    def create_test_pdf_content(self):
        """Create a simple PDF-like content for testing."""
        # This is a minimal PDF content - in real tests you might use a proper PDF library
        return b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n173\n%%EOF"
    
    @patch('app.routers.upload.evaluate_candidate_and_create')
    @patch('app.routers.upload.convert_from_bytes')
    @patch('app.routers.upload.store_file')
    def test_upload_files_new_candidate_success(self, mock_store_file, mock_convert, mock_evaluate):
        """Test successful file upload for new candidate."""
        # Setup mocks
        mock_convert.return_value = [MagicMock()]  # Mock image
        mock_evaluate.return_value = AsyncMock()
        mock_store_file.return_value = "/test/path/file.pdf"
        
        # Create test job
        job = self.create_test_job("Software Engineer")
        
        # Create test file
        pdf_content = self.create_test_pdf_content()
        files = [("pdf_files", ("test_resume.pdf", BytesIO(pdf_content), "application/pdf"))]
        data = {"job_title": "Software Engineer"}
        
        response = self.client.post("/api/upload", files=files, data=data)
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("resumes processed", response_data["message"])
        self.assertEqual(len(response_data["processed_files"]), 1)
        self.assertIn("test_resume.pdf", response_data["processed_files"])
    
    @patch('app.routers.upload.convert_from_bytes')
    def test_upload_files_invalid_file_type(self, mock_convert):
        """Test upload with invalid file type."""
        # Create test job
        self.create_test_job("Software Engineer")
        
        # Create non-PDF file
        files = [("pdf_files", ("test.txt", BytesIO(b"text content"), "text/plain"))]
        data = {"job_title": "Software Engineer"}
        
        response = self.client.post("/api/upload", files=files, data=data)
        
        # Should return 400 since no valid files were processed
        self.assertEqual(response.status_code, 400)
        self.assertIn("No new valid PDF files", response.json()["message"])
        
        # Convert should not be called for invalid files
        mock_convert.assert_not_called()
    
    @patch('app.routers.upload.evaluate_candidate_and_create')
    @patch('app.routers.upload.convert_from_bytes')
    @patch('app.routers.upload.store_file')
    def test_upload_files_existing_candidate_new_job(self, mock_store_file, mock_convert, mock_evaluate):
        """Test upload for existing candidate applying to new job."""
        # Setup mocks
        mock_convert.return_value = [MagicMock()]
        mock_evaluate.return_value = AsyncMock()
        mock_store_file.return_value = "/test/path/file.pdf"
        
        # Create test data
        job = self.create_test_job("Software Engineer")
        pdf_content = self.create_test_pdf_content()
        resume_hash = "b8f4d4e29b6e3c5a8d7e2f1a9c6b4e8d3f2a1b9c7e5d4f8a6b3e9c2d1f7e4a8b"
        
        # Create existing candidate
        self.create_test_candidate(resume_hash=resume_hash)
        
        files = [("pdf_files", ("resume.pdf", BytesIO(pdf_content), "application/pdf"))]
        data = {"job_title": "Software Engineer"}
        
        response = self.client.post("/api/upload", files=files, data=data)
        
        self.assertEqual(response.status_code, 200)
        # Should process the file since candidate hasn't applied to this job
        response_data = response.json()
        self.assertIn("processed", response_data["message"])
    
    def test_upload_files_missing_job_title(self):
        """Test upload without job title."""
        pdf_content = self.create_test_pdf_content()
        files = [("pdf_files", ("test_resume.pdf", BytesIO(pdf_content), "application/pdf"))]
        
        response = self.client.post("/api/upload", files=files)
        
        self.assertEqual(response.status_code, 422)  # Validation error
    
    def test_upload_files_no_files(self):
        """Test upload without any files."""
        data = {"job_title": "Software Engineer"}
        
        response = self.client.post("/api/upload", data=data)
        
        self.assertEqual(response.status_code, 422)  # Validation error
    
    @patch('app.routers.upload.convert_from_bytes')
    def test_upload_files_pdf_conversion_error(self, mock_convert):
        """Test handling of PDF conversion errors."""
        # Setup mock to raise conversion error
        mock_convert.side_effect = Exception("PDF conversion failed")
        
        # Create test job
        self.create_test_job("Software Engineer")
        
        pdf_content = self.create_test_pdf_content()
        files = [("pdf_files", ("test_resume.pdf", BytesIO(pdf_content), "application/pdf"))]
        data = {"job_title": "Software Engineer"}
        
        response = self.client.post("/api/upload", files=files, data=data)
        
        # Should return 500 or appropriate error code
        self.assertNotEqual(response.status_code, 200)


class TestStatusRoutes(TestRoutes):
    """Test suite for /api/status routes."""
    
    def test_get_status_success(self):
        """Test successful status endpoint."""
        response = self.client.get("/api/status")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["environment"], "test")
        self.assertIn("model_endpoint", data)
        self.assertEqual(data["model_endpoint"], "local_vllm")  # In test/dev mode
    
    @patch('app.process.vllm_model', new=MagicMock())
    def test_health_check_success(self):
        """Test successful health check in dev mode."""
        response = self.client.get("/api/health")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["dependencies"]["ai_model"], "ok")
    
    @patch('app.process.vllm_model', new=None)
    def test_health_check_ai_model_error(self):
        """Test health check with AI model error in dev mode."""
        response = self.client.get("/api/health")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["dependencies"]["ai_model"], "error")
    
    @patch('app.llm_client.vllm_model', new=None)
    def test_health_check_ai_model_unreachable(self):
        """Test health check with unavailable AI model in dev mode."""
        response = self.client.get("/api/health")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["dependencies"]["ai_model"], "error")


class TestUserRoutes(TestRoutes):
    """Test suite for /api/user routes."""
    
    def test_get_user_success(self):
        """Test successful user endpoint."""
        response = self.client.get("/api/user")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify mock user data
        self.assertEqual(data["id"], 99)
        self.assertEqual(data["name"], "Sarah Johnson")
        self.assertEqual(data["email"], "sarah.johnson@company.com")
        self.assertIn("created_at", data)


class TestRootRoute(TestRoutes):
    """Test suite for root route."""
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = self.client.get("/")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("Welcome", data["message"])


class TestErrorHandling(TestRoutes):
    """Test suite for error handling scenarios."""
    
    def test_invalid_route(self):
        """Test accessing non-existent route."""
        response = self.client.get("/api/nonexistent")
        
        self.assertEqual(response.status_code, 404)
    
    def test_invalid_method(self):
        """Test using invalid HTTP method."""
        response = self.client.delete("/api/status")
        
        self.assertEqual(response.status_code, 405)  # Method not allowed
    
    def test_malformed_json(self):
        """Test sending malformed JSON."""
        response = self.client.post(
            "/api/jobs",
            content="invalid json{",
            headers={"Content-Type": "application/json"}
        )
        
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main(verbosity=2)
