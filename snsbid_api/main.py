from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, bid, predict, staff, batch

app = FastAPI(title="snsbid API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,    prefix="/api/auth",    tags=["auth"])
app.include_router(bid.router,     prefix="/api/bids",    tags=["bids"])
app.include_router(predict.router, prefix="/api/predict", tags=["predict"])
app.include_router(staff.router,   prefix="/api/staff",   tags=["staff"])
app.include_router(batch.router,   prefix="/api/batch",   tags=["batch"])

@app.get("/")
def root():
    return {"status": "ok"}