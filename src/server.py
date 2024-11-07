from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging
from .api import generate_topology as topology_generator
import json
from .logger_config import setup_logger
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
from typing import List, Dict
from routes import maps

# 配置日志
logger = setup_logger(__name__, '/var/log/topo-planner/topo-planner.log')

app = FastAPI()

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "Authorization"],
)

app.mount("/static", StaticFiles(directory="/app/static"), name="static")

app.include_router(maps.router, prefix="/api/maps", tags=["maps"])

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