from fastapi import FastAPI

from .api.v1 import biens, loyers, quitus

app = FastAPI(title="SCI Manager API")

@app.get("/")
def read_root():
    return {"message": "SCI Manager is running"}

app.include_router(biens.router, prefix="/v1/biens", tags=["biens"])
app.include_router(loyers.router, prefix="/v1/loyers", tags=["loyers"])
app.include_router(quitus.router, prefix="/v1/quitus", tags=["quitus"])
