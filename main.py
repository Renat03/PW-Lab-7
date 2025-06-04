from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
import secrets

app = FastAPI()

SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 5

users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        "permissions": ["READ", "WRITE", "DELETE"]
    },
    "user": {
        "username": "user",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        "permissions": ["READ"]
    }
}

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    permissions: List[str] = []

class User(BaseModel):
    username: str
    permissions: List[str]

class UserInDB(User):
    hashed_password: str

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user(username: str) -> Optional[UserInDB]:
    user_dict = users_db.get(username)
    if user_dict:
        return UserInDB(**user_dict)
    return None

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        permissions: List[str] = payload.get("permissions", [])
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, permissions=permissions)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def check_permission(permission: str, user: User = Depends(get_current_user)):
    if permission not in user.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing {permission} permission",
        )

workouts_db = []

class WorkoutBase(BaseModel):
    name: str
    date: str
    startTime: str
    endTime: str
    rating: Optional[int] = None
    comment: Optional[str] = None

class WorkoutCreate(WorkoutBase):
    pass

class Workout(WorkoutBase):
    id: str
    exercises: List[dict] = []

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "permissions": user.permissions},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/workouts/", response_model=List[Workout])
async def read_workouts(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    user: User = Depends(get_current_user)
):
    await check_permission("READ", user)
    return workouts_db[skip : skip + limit]

@app.post("/workouts/", response_model=Workout, status_code=status.HTTP_201_CREATED)
async def create_workout(
    workout: WorkoutCreate,
    user: User = Depends(get_current_user)
):
    await check_permission("WRITE", user)
    workout_id = f"{len(workouts_db)}_{secrets.token_urlsafe(4)}"
    workout_dict = workout.dict()
    workout_dict["id"] = workout_id
    workout_dict["exercises"] = []
    workouts_db.append(workout_dict)
    return workout_dict

@app.get("/workouts/{workout_id}", response_model=Workout)
async def read_workout(
    workout_id: str,
    user: User = Depends(get_current_user)
):
    await check_permission("READ", user)
    for workout in workouts_db:
        if workout["id"] == workout_id:
            return workout
    raise HTTPException(status_code=404, detail="Workout not found")

@app.put("/workouts/{workout_id}", response_model=Workout)
async def update_workout(
    workout_id: str,
    workout: WorkoutCreate,
    user: User = Depends(get_current_user)
):
    await check_permission("WRITE", user)
    for idx, existing_workout in enumerate(workouts_db):
        if existing_workout["id"] == workout_id:
            updated_workout = workout.dict()
            updated_workout["id"] = workout_id
            updated_workout["exercises"] = existing_workout["exercises"]
            workouts_db[idx] = updated_workout
            return updated_workout
    raise HTTPException(status_code=404, detail="Workout not found")

@app.delete("/workouts/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workout(
    workout_id: str,
    user: User = Depends(get_current_user)
):
    await check_permission("DELETE", user)
    for idx, workout in enumerate(workouts_db):
        if workout["id"] == workout_id:
            workouts_db.pop(idx)
            return
    raise HTTPException(status_code=404, detail="Workout not found")

class Exercise(BaseModel):
    name: str
    category: str

class ExerciseSet(BaseModel):
    reps: int
    weight: float

# Add below existing routes

@app.post("/workouts/{workout_id}/exercises", status_code=status.HTTP_201_CREATED)
async def add_exercise(
    workout_id: str,
    exercise: Exercise,
    user: User = Depends(get_current_user)
):
    await check_permission("WRITE", user)
    for workout in workouts_db:
        if workout["id"] == workout_id:
            exercise_id = str(len(workout["exercises"])) + secrets.token_urlsafe(4)
            exercise_dict = exercise.dict()
            exercise_dict["id"] = exercise_id
            exercise_dict["sets"] = []
            workout["exercises"].append(exercise_dict)
            return exercise_dict
    raise HTTPException(status_code=404, detail="Workout not found")
