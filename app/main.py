from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import io
import time
import asyncio
from typing import Optional, Literal
from PIL import Image
from rembg import remove, new_session
import logging
from concurrent.futures import ThreadPoolExecutor
import base64
from .models import HealthResponse, BackgroundRemovalResponse
from .utils import validate_image, process_image_with_rembg

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app with enhanced metadata
app = FastAPI(
    title="Background Removal API",
    description="AI-powered background removal service using rembg with enhanced CORS support",
    version="1.0.1",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "health",
            "description": "Health check and status endpoints",
        },
        {
            "name": "background-removal",
            "description": "Background removal operations",
        },
    ]
)

# Enhanced CORS configuration for Azure Container Apps
import os

# Allow all origins
ALLOWED_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Cache-Control",
        "Pragma",
        "X-Processing-Time",
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Headers"
    ],
    expose_headers=["X-Processing-Time", "Content-Disposition"],
    max_age=3600,
)

# Add trusted host middleware for additional security
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Global variables for optimization
rembg_session = None
executor = ThreadPoolExecutor(max_workers=4)  # For CPU-intensive tasks

@app.on_event("startup")
async def startup_event():
    """Initialize rembg session and resources on startup"""
    global rembg_session
    try:
        logger.info("Initializing background removal service...")
        
        # Initialize rembg session in a separate thread to avoid blocking
        loop = asyncio.get_event_loop()
        rembg_session = await loop.run_in_executor(
            executor, 
            lambda: new_session('u2net')  # Specify model for better performance
        )
        
        logger.info("Rembg session initialized successfully with u2net model")
        logger.info("Background Removal API startup completed")
        
    except Exception as e:
        logger.error(f"Failed to initialize rembg session: {str(e)}")
        raise RuntimeError(f"Startup failed: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    logger.info("Shutting down Background Removal API...")
    executor.shutdown(wait=True)
    logger.info("Cleanup completed")


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Comprehensive health check with service validation"""
    try:
        # Test rembg session availability
        if rembg_session is None:
            raise Exception("Rembg session not initialized")
        
        # Test executor availability
        if executor._shutdown:
            raise Exception("Thread executor is shutdown")
        
        return HealthResponse(
            status="healthy",
            message="All services are operational - Ready to process images",
            version="1.0.1"
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503, 
            detail=f"Service unavailable: {str(e)}"
        )


# Add OPTIONS handler for preflight requests
@app.options("/remove-background")
async def remove_background_options():
    """Handle preflight OPTIONS requests for remove-background endpoint"""
    return {"message": "OK"}

@app.options("/remove-background-base64") 
async def remove_background_base64_options():
    """Handle preflight OPTIONS requests for remove-background-base64 endpoint"""
    return {"message": "OK"}

@app.post("/remove-background", tags=["background-removal"])
async def remove_background(
    file: UploadFile = File(
        ..., 
        description="Image file to process (PNG, JPG, JPEG, WEBP)",
        media_type="image/*"
    ),
    output_format: Literal["PNG", "WEBP"] = Form(
        default="PNG",
        description="Output image format"
    ),
    quality: Optional[int] = Form(
        default=95,
        description="Output quality for WEBP format (1-100)",
        ge=1,
        le=100
    )
):
    """
    Remove background from uploaded image and return processed image
    
    This endpoint processes the uploaded image to remove its background,
    returning a new image with transparent background.
    
    Args:
        file: Image file to process (supports PNG, JPG, JPEG, WEBP)
        output_format: Output format - PNG (lossless) or WEBP (compressed)
        quality: Quality setting for WEBP output (1-100, higher is better)
    
    Returns:
        StreamingResponse: Processed image with transparent background
    """
    start_time = time.time()
    original_filename = file.filename or "image"
    
    try:
        logger.info(f"Processing background removal for: {original_filename}")
        
        # Validate uploaded file
        await validate_image(file)
        
        # Read image data
        image_data = await file.read()
        logger.info(f"Read {len(image_data)} bytes from uploaded file")
        
        # Process image using thread executor for CPU-intensive work
        loop = asyncio.get_event_loop()
        processed_image = await loop.run_in_executor(
            executor,
            lambda: process_image_sync(image_data, output_format, quality)
        )
        
        # Calculate processing metrics
        processing_time = time.time() - start_time
        logger.info(f"Background removal completed in {processing_time:.2f}s")
        
        # Determine content type and filename
        content_type = "image/png" if output_format.upper() == "PNG" else "image/webp"
        file_extension = output_format.lower()
        output_filename = f"no_bg_{original_filename.rsplit('.', 1)[0]}.{file_extension}"
        
        # Return processed image with enhanced headers
        return StreamingResponse(
            io.BytesIO(processed_image),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={output_filename}",
                "X-Processing-Time": f"{processing_time:.2f}s",
                "X-Original-Size": str(len(image_data)),
                "X-Output-Size": str(len(processed_image)),
                "X-Output-Format": output_format.upper(),
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        
    except HTTPException as e:
        logger.warning(f"Validation error for {original_filename}: {e.detail}")
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Background removal failed for {original_filename} after {processing_time:.2f}s: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Background removal failed: {str(e)}"
        )

@app.post("/remove-background-base64", response_model=BackgroundRemovalResponse, tags=["background-removal"])
async def remove_background_base64(
    file: UploadFile = File(
        ..., 
        description="Image file to process",
        media_type="image/*"
    ),
    output_format: Literal["PNG", "WEBP"] = Form(
        default="PNG",
        description="Output image format"
    ),
    quality: Optional[int] = Form(
        default=95,
        description="Output quality for WEBP format (1-100)",
        ge=1,
        le=100
    )
):
    """
    Remove background and return base64 encoded result
    
    This endpoint processes the uploaded image and returns the result
    as a base64 encoded string in a JSON response.
    
    Args:
        file: Image file to process
        output_format: Output format (PNG or WEBP)  
        quality: Quality setting for WEBP output (1-100)
    
    Returns:
        BackgroundRemovalResponse: JSON response with base64 encoded image
    """
    start_time = time.time()
    original_filename = file.filename or "image"
    
    try:
        logger.info(f"Processing base64 background removal for: {original_filename}")
        
        # Validate uploaded file
        await validate_image(file)
        
        # Read image data
        image_data = await file.read()
        original_size = len(image_data)
        
        # Process image using thread executor
        loop = asyncio.get_event_loop()
        processed_image = await loop.run_in_executor(
            executor,
            lambda: process_image_sync(image_data, output_format, quality)
        )
        
        # Convert to base64
        base64_image = base64.b64encode(processed_image).decode('utf-8')
        
        # Calculate processing metrics
        processing_time = time.time() - start_time
        output_size = len(processed_image)
        
        logger.info(
            f"Base64 background removal completed for {original_filename} "
            f"in {processing_time:.2f}s (size: {original_size} -> {output_size} bytes)"
        )
        
        return BackgroundRemovalResponse(
            success=True,
            message=f"Background removed successfully from {original_filename}",
            base64_image=base64_image,
            processing_time=processing_time,
            output_format=output_format.lower(),
            original_size=original_size,
            output_size=output_size,
            compression_ratio=round((1 - output_size / original_size) * 100, 2) if output_size < original_size else 0
        )
        
    except HTTPException as e:
        logger.warning(f"Validation error for {original_filename}: {e.detail}")
        processing_time = time.time() - start_time
        return BackgroundRemovalResponse(
            success=False,
            message=f"Validation failed: {e.detail}",
            base64_image="",
            processing_time=processing_time,
            output_format="",
            original_size=0,
            output_size=0,
            compression_ratio=0
        )
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Background removal failed for {original_filename} after {processing_time:.2f}s: {str(e)}")
        return BackgroundRemovalResponse(
            success=False,
            message=f"Background removal failed: {str(e)}",
            base64_image="",
            processing_time=processing_time,
            output_format="",
            original_size=0,
            output_size=0,
            compression_ratio=0
        )

def process_image_sync(image_data: bytes, output_format: str, quality: int = 95) -> bytes:
    """
    Synchronous image processing function for use in thread executor
    
    Args:
        image_data: Raw image bytes
        output_format: Output format (PNG or WEBP)
        quality: Quality for WEBP output
    
    Returns:
        bytes: Processed image data
    """
    global rembg_session
    
    if rembg_session is None:
        raise RuntimeError("Rembg session not initialized")
    
    # Remove background using rembg
    output_image = remove(image_data, session=rembg_session)
    
    # Convert to PIL Image for format conversion and optimization
    img = Image.open(io.BytesIO(output_image))
    
    # Ensure image has transparency
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Save in requested format with optimization
    output_buffer = io.BytesIO()
    
    if output_format.upper() == "PNG":
        # PNG optimization
        img.save(
            output_buffer, 
            format="PNG", 
            optimize=True,
            compress_level=6  # Good balance of speed vs compression
        )
    else:  # WEBP
        # WEBP with quality control
        img.save(
            output_buffer,
            format="WEBP", 
            quality=quality,
            method=6,  # Best compression method
            lossless=False if quality < 100 else True
        )
    
    return output_buffer.getvalue()

# Enhanced error handling middleware
@app.middleware("http")
async def error_handling_middleware(request, call_next):
    """Global error handling and request logging"""
    start_time = time.time()
    
    try:
        # Log incoming request
        logger.info(f"Incoming {request.method} request to {request.url.path}")
        
        response = await call_next(request)
        
        # Log response time
        process_time = time.time() - start_time
        logger.info(f"Request completed in {process_time:.2f}s with status {response.status_code}")
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Unhandled error after {process_time:.2f}s: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred"
        )

if __name__ == "__main__":
    import uvicorn
    
    # Enhanced uvicorn configuration
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        workers=1,  # Single worker for shared rembg session
        log_level="info",
        access_log=True,
        reload=False  # Set to True only in development
    )
