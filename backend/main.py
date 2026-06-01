from fastapi import FastAPI, HTTPException, status, Request
from schemas import UserCreate, UserResponse
app = FastAPI()

start_base = [
    {"id": 1, "name": "David", "lastname" : "papidze", "age" : 22},
    {"id": 2, "name": "elene", "lastname" : "qoi", "age" : 25},
    {"id": 3, "name": "giorgi", "lastname" : "ruxaia", "age" : 30},
    {"id": 4, "name": "saba", "lastname" : "vezdeni", "age" : 28},
    {"id": 5, "name": "elene", "lastname" : "gurgenidze", "age" : 35},
    {"id": 6, "name": "giorgi", "lastname" : "paqsashvili", "age" : 40},
    {"id": 7, "name": "beka", "lastname" : "taru", "age" : 33},
    {"id": 8, "name": "saba", "lastname" : "natsvlishvili", "age" : 29}
]

@app.get("/")
@app.get("/users", response_model = list[UserResponse])
def get_all_users():
    return start_base

@app.get("/users/{id}", response_model = UserResponse)
def get_user(id: int):
    for i in start_base:
        if i.get('id') == id:
            return i
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

@app.post("/CreateUser", response_model= UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate):
    new_id = max(p["id"] for p in start_base) + 1
    new_user = {
        "id": new_id,
        "name" : user.name,
        "last_name" : user.last_name,
        "age" : user.age,
        "date_created" : "random"
    }
    start_base.append(new_user)
    return new_user

