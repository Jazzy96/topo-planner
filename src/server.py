from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware import Middleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from .api import generate_topology as topology_generator
from .maps import router as maps_router
import json
from .logger_config import setup_logger
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
from typing import List, Dict

# 配置日志
logger = setup_logger(__name__, '/var/log/topo-planner/topo-planner.log')

class CSPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://maps.googleapis.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://*.googleapis.com https://*.gstatic.com; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "connect-src 'self' https://*.googleapis.com"
        )
        return response

app = FastAPI(middleware=[
    Middleware(CSPMiddleware),
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["POST", "GET", "OPTIONS"],
        allow_headers=["Content-Type", "Accept", "Authorization"],
    )
])

app.mount("/static", StaticFiles(directory="/app/static"), name="static")

app.include_router(maps_router, prefix="/api/maps", tags=["maps"])

@app.get("/", response_class=HTMLResponse)
async def get_index():
    return open('/app/static/index.html').read()

@app.get("/api/results")
async def get_results():
    result_dir = "/app/results"
    results = []
    
    if os.path.exists(result_dir):
        for file in sorted(os.listdir(result_dir), reverse=True):
            if file.endswith('.json'):
                filepath = os.path.join(result_dir, file)
                with open(filepath, 'r') as f:
                    data = json.load(f)
                results.append({
                    'filename': file,
                    'data': data
                })
    
    return results

@app.get("/api/result/{filename}")
async def get_result(filename: str):
    filepath = os.path.join("/app/results", filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Result not found")
        
    with open(filepath, 'r') as f:
        return json.load(f)

class TopologyRequest(BaseModel):
    nodes_json: str
    edges_json: str
    config_json: str = None

@app.post("/generate_topology")
async def handle_topology_request(request: TopologyRequest):
    try:
        logger.debug(f"接收到请求数据: nodes_json长度={len(request.nodes_json)}, "
                    f"edges_json长度={len(request.edges_json)}")
        
        result = topology_generator(
            request.nodes_json,
            request.edges_json,
            request.config_json
        )
        
        return {
            "status": "success",
            "data": json.loads(result)
        }
    
    except Exception as e:
        logger.error(f"处理请求时发生错误: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(
        "src.server:app",
        host="0.0.0.0",
        port=8080,
        log_level="debug",
        reload=True
    ) 