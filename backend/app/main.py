from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.config import settings
from app.admin_routes import router as admin_router
from app.detector import CameraDetector
from app.test_routes import router as test_router


app = FastAPI(title="Seguridad V2 API")
detector = CameraDetector()
app.include_router(admin_router)
app.include_router(test_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_origin,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    detector.start()


@app.on_event("shutdown")
def shutdown():
    detector.stop()


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/camera/status")
def camera_status():
    return detector.status()


@app.get("/camera/stream")
def camera_stream():
    return StreamingResponse(
        detector.stream(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
