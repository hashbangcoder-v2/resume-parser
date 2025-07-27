from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import candidates, status, user, upload
from .db import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS configuration
origins = [
    "http://localhost:3000",  # The default Next.js dev port
    "http://localhost:5173", # The default Vite dev port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(candidates.router)
app.include_router(status.router)
app.include_router(user.router)
app.include_router(upload.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Wheat-From-Chaff API"} 