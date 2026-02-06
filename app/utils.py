from fastapi import UploadFile, HTTPException
from PIL import Image
from rembg import remove
import io
import logging

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

async def validate_image(file: UploadFile):
    """Validate uploaded image file"""
    
    # Check file extension
    file_ext = file.filename.lower().split('.')[-1] if file.filename else ''
    if f'.{file_ext}' not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check content type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail="Invalid content type. Please upload an image file."
        )
    
    # Check file size (read a bit to get size)
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Reset file pointer
    await file.seek(0)

async def process_image_with_rembg(image_data: bytes, session, output_format: str = "PNG") -> bytes:
    """Process image with rembg to remove background"""
    
    try:
        # Open image with PIL
        input_image = Image.open(io.BytesIO(image_data))
        
        # Remove background
        output_image = remove(input_image, session=session)
        
        # Convert to desired format
        output_buffer = io.BytesIO()
        
        if output_format.upper() == "WEBP":
            output_image.save(output_buffer, format="WEBP", quality=95)
        else:
            output_image.save(output_buffer, format="PNG")
        
        return output_buffer.getvalue()
        
    except Exception as e:
        logger.error(f"Image processing failed: {str(e)}")
        raise Exception(f"Image processing failed: {str(e)}")
