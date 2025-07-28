import os
from sqlalchemy.orm import Session
from datetime import datetime
from app.db import get_db, engine, Base
from app.models import Job, Candidate, Application

# Mock data from frontend
mock_data = {
    "Senior Software Engineer": [
        {
            "id": 1,
            "name": "Alice Johnson",
            "email": "alice.j@example.com",
            "lastUpdated": "2024-01-15 14:30",
            "status": "Shortlisted",
            "finalStatus": "Shortlisted",
            "appliedOn": "12-01-2024 09:15",
            "reason": "Strong technical background, excellent problem-solving skills",
            "fileUrl": "/files/alice-johnson-resume.pdf",
        },
        {
            "id": 2,
            "name": "Bob Smith",
            "email": "bob.s@example.com",
            "lastUpdated": "2024-01-15 11:20",
            "status": "Needs Review",
            "finalStatus": "Needs Review",
            "appliedOn": "10-01-2024 16:45",
            "reason": "Good experience but needs technical assessment",
            "fileUrl": "/files/bob-smith-resume.pdf",
        },
    ],
    "Product Manager": [
        {
            "id": 1,
            "name": "Frank Thompson",
            "email": "frank.t@example.com",
            "lastUpdated": "2024-01-15 15:20",
            "status": "Shortlisted",
            "finalStatus": "Shortlisted",
            "appliedOn": "14-01-2024 10:15",
            "reason": "Strong product strategy experience and leadership skills",
            "fileUrl": "/files/frank-thompson-resume.pdf",
        },
    ],
    "UX Designer": [
        {
            "id": 1,
            "name": "Henry Chang",
            "email": "henry.c@example.com",
            "lastUpdated": "2024-01-15 14:45",
            "status": "Shortlisted",
            "finalStatus": "Shortlisted",
            "appliedOn": "13-01-2024 09:30",
            "reason": "Outstanding portfolio with user-centered design approach",
            "fileUrl": "/files/henry-chang-portfolio.pdf",
        },
        {
            "id": 2,
            "name": "Iris Rodriguez",
            "email": "iris.r@example.com",
            "lastUpdated": "2024-01-15 10:15",
            "status": "Rejected",
            "finalStatus": "Rejected",
            "appliedOn": "09-01-2024 14:20",
            "reason": "Portfolio doesn't align with our design standards",
            "fileUrl": "/files/iris-rodriguez-portfolio.pdf",
        },
    ],
}

def seed_database():
    # Create tables
    Base.metadata.create_all(bind=engine)

    db = next(get_db())

    try:
        # Add Jobs
        jobs = {}
        for job_title in mock_data.keys():
            if not db.query(Job).filter(Job.title == job_title).first():
                job = Job(title=job_title, description=f"Description for {job_title}")
                db.add(job)
                db.commit()
                db.refresh(job)
                jobs[job_title] = job
            else:
                jobs[job_title] = db.query(Job).filter(Job.title == job_title).first()

        # Add Candidates and Applications
        for job_title, candidates_list in mock_data.items():
            job = jobs[job_title]
            for candidate_data in candidates_list:
                # Check if candidate exists
                candidate = db.query(Candidate).filter(Candidate.email == candidate_data["email"]).first()
                if not candidate:
                    candidate = Candidate(
                        name=candidate_data["name"],
                        email=candidate_data["email"],
                    )
                    db.add(candidate)
                    db.commit()
                    db.refresh(candidate)

                # Check if application exists
                application = db.query(Application).filter(
                    Application.job_id == job.id,
                    Application.candidate_id == candidate.id
                ).first()

                if not application:
                    applied_on = datetime.strptime(candidate_data["appliedOn"], "%d-%m-%Y %H:%M")
                    last_updated_str = candidate_data["lastUpdated"]
                    
                    # The format of lastUpdated in mock data is YYYY-MM-DD HH:MM
                    last_updated = datetime.strptime(last_updated_str, "%Y-%m-%d %H:%M")
                    
                    application = Application(
                        job_id=job.id,
                        candidate_id=candidate.id,
                        status=candidate_data["status"],
                        final_status=candidate_data["finalStatus"],
                        reason=candidate_data["reason"],
                        file_url=candidate_data["fileUrl"],
                        applied_on=applied_on,
                        last_updated=last_updated,
                    )
                    db.add(application)
        
        db.commit()
        print("Database seeded successfully!")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database() 