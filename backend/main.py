from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

SECRET_KEY = os.getenv('SECRET_KEY', 'edulinks-secret-key')
serializer = URLSafeTimedSerializer(SECRET_KEY)

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./edulinks.db')
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False}, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./edulinks.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String, default="instructor")
    created_at = Column(DateTime, default=datetime.utcnow)

class Posting(Base):
    __tablename__ = "postings"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    subject = Column(String)
    region = Column(String)
    rate = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True, index=True)
    posting_id = Column(Integer, ForeignKey("postings.id"))
    instructor_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic models
class UserCreate(BaseModel):
    email: str
    password: str
    role: str = "instructor"

class UserResponse(BaseModel):
    id: int
    email: str
    role: str

class LoginRequest(BaseModel):
    email: str
    password: str

class PostingCreate(BaseModel):
    title: str
    subject: str
    region: str
    rate: int

class PostingResponse(BaseModel):
    id: int
    title: str
    subject: str
    region: str
    rate: int

class ApplicationCreate(BaseModel):
    posting_id: int

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Simple auth (for demo)
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    # Simple token validation (demo only)
    token = credentials.credentials
    if token != "demo_token":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    # Return mock user
    return {"id": 1, "email": "demo@example.com", "role": "instructor"}

# Routes
@app.post("/auth/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = User(email=user.email, password=user.password, role=user.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/auth/login")
def login(credentials: LoginRequest):
    # Simple login (in real app, verify password and user table)
    if credentials.email == "demo@example.com" and credentials.password == "password":
        return {"access_token": "demo_token", "token_type": "bearer"}
    # fallback check DB if user exists
    db = next(get_db())
    user = db.query(User).filter(User.email == credentials.email, User.password == credentials.password).first()
    if user:
        return {"access_token": "demo_token", "token_type": "bearer"}
    raise HTTPException(status_code=400, detail="Invalid credentials")

@app.get("/auth/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user

@app.get("/postings", response_model=list[PostingResponse])
def get_postings(db: Session = Depends(get_db)):
    postings = db.query(Posting).all()
    return postings

@app.post("/postings", response_model=PostingResponse)
def create_posting(posting: PostingCreate, db: Session = Depends(get_db)):
    new_posting = Posting(**posting.dict())
    db.add(new_posting)
    db.commit()
    db.refresh(new_posting)
    return new_posting

@app.post("/applications")
def apply_to_posting(application: ApplicationCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    new_application = Application(posting_id=application.posting_id, instructor_id=current_user["id"])
    db.add(new_application)
    db.commit()
    return {"message": "Application submitted"}

@app.get("/applications")
def get_applications(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    applications = db.query(Application).filter(Application.instructor_id == current_user["id"]).all()
    return applications

# Create tables
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "EDULINKS API is running"}


