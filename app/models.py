from pydantic import BaseModel
from typing import Optional

class HealthResponse(BaseModel):
    status: str
    message: str
    version: str

class BackgroundRemovalResponse(BaseModel):
    success: bool
    message: str
    base64_image: str
    processing_time: float
    output_format: str
    original_size: Optional[int] = 0
    output_size: Optional[int] = 0
    compression_ratio: Optional[float] = 0
