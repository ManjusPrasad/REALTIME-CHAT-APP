from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

SECRET_KEY = "supersecretkey"  # Change this in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

router = APIRouter()

fake_users_db = {}  # username: {username, hashed_password}

class User(BaseModel):
    username: str

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class RegisterRequest(BaseModel):
    username: str
    password: str

@router.post("/register", response_model=User)
def register(data: RegisterRequest):
    if data.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="Password too short (min 8 chars)")
    hashed = pwd_context.hash(data.password)
    fake_users_db[data.username] = {"username": data.username, "hashed_password": hashed}
    return User(username=data.username)

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user or not pwd_context.verify(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = fake_users_db.get(username)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return User(username=username)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def verify_token(token: str) -> str:
    """Verify a raw JWT token string and return the username (sub) or raise HTTPException."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        if username not in fake_users_db:
            raise HTTPException(status_code=401, detail="User not found")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
