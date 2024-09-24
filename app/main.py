from fastapi import FastAPI
from routers import matches

app = FastAPI()

app.include_router(matches.router)

@app.get("/")
def hello_world():
    return {"Hello": "World"}