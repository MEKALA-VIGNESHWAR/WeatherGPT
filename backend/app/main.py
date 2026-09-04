import time
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import setup_logging, get_logger, request_id_ctx_var, generate_request_id
from app.core.database import init_db
from app.api.v1.auth import router as auth_router
from app.api.v1.weather import router as weather_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.chat import router as chat_router
from app.api.v1.locations import router as locations_router
from app.api.v1.advisories import router as advisories_router
from app.api.v1.climate import router as climate_router
from app.api.v1.map import router as map_router
from app.api.v1.voice import router as voice_router
from app.api.v1.admin import router as admin_router
from app.alerts.alert_service import warning_service

setup_logging()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up WeatherGPT Backend Service...")
    init_db()
    yield
    logger.info("Shutting down WeatherGPT Backend Service...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Conversational Weather Intelligence & Decision-Support Platform (SIH 2026)",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID and Latency Middleware
@app.middleware("http")
async def request_tracing_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID") or generate_request_id()
    token = request_id_ctx_var.set(req_id)
    t0 = time.time()
    
    try:
        response = await call_next(request)
        latency = (time.time() - t0) * 1000
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Response-Time-Ms"] = f"{latency:.2f}"
        return response
    except Exception as exc:
        logger.error(f"Unhandled server error during request {req_id}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "request_id": req_id,
                "message": "An unexpected error occurred while processing the weather intelligence request."
            },
            headers={"X-Request-ID": req_id}
        )
    finally:
        request_id_ctx_var.reset(token)


# Health Check
@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "demo_mode": settings.DEMO_MODE,
        "environment": settings.ENVIRONMENT
    }


# WebSocket Manager for Real-Time Alert Broadcasts
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass


ws_manager = ConnectionManager()


@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        # Immediately send active warnings on connect
        active = warning_service.get_alerts_for_location(17.3850, 78.4867)
        await websocket.send_text(json.dumps({
            "type": "INITIAL_ALERTS",
            "data": active.model_dump()
        }, default=str))

        while True:
            # Keep-alive heartbeat ping/pong
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


# Mount API v1 Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(weather_router, prefix=settings.API_V1_STR)
app.include_router(alerts_router, prefix=settings.API_V1_STR)
app.include_router(chat_router, prefix=settings.API_V1_STR)
app.include_router(locations_router, prefix=settings.API_V1_STR)
app.include_router(advisories_router, prefix=settings.API_V1_STR)
app.include_router(climate_router, prefix=settings.API_V1_STR)
app.include_router(map_router, prefix=settings.API_V1_STR)
app.include_router(voice_router, prefix=settings.API_V1_STR)
app.include_router(admin_router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
