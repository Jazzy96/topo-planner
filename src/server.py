from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging
from .api import generate_topology as topology_generator
import json
from .logger_config import setup_logger

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