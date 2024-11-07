from fastapi import APIRouter, HTTPException
from typing import Dict
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

router = APIRouter()

@router.get("/key", response_model=Dict[str, str])
async def get_maps_key():
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="Google Maps API key not configured"
        )
    return {"key": api_key} 