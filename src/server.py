from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from .api import generate_topology as topology_generator

app = FastAPI()

class TopologyRequest(BaseModel):
    nodes_json: str
    edges_json: str
    config_json: str = None

@app.post("/generate_topology")
async def handle_topology_request(request: TopologyRequest):
    try:
        result = topology_generator(
            request.nodes_json,
            request.edges_json,
            request.config_json
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "src.server:app", 
        host="0.0.0.0", 
        port=8080,
        reload=True  # 启用热重载
    ) 