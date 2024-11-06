from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from .api import generate_mesh_topology

app = FastAPI()

class TopologyRequest(BaseModel):
    nodes_json: str
    edges_json: str
    config_json: str = None

@app.post("/generate_topology")
async def generate_topology(request: TopologyRequest):
    try:
        result = generate_mesh_topology(
            request.nodes_json,
            request.edges_json,
            request.config_json
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080) 