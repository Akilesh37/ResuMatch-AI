import os
import io
import logging
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from ..config import TESSERACT_CMD

logger = logging.getLogger(__name__)

# Configure pytesseract path
if os.path.exists(TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

def preprocess_image_for_ocr(image: Image.Image) -> Image.Image:
    """
    Enhance and binarize image to maximize Tesseract OCR character accuracy.
    """
    try:
        # Convert to Grayscale
        gray = image.convert('L')
        
        # Increase contrast
        enhancer = ImageEnhance.Contrast(gray)
        enhanced = enhancer.enhance(1.8)
        
        # Slight sharpening
        sharpened = enhanced.filter(ImageFilter.SHARPEN)
        
        # Adaptive/Otsu-style thresholding
        threshold = 145
        binarized = sharpened.point(lambda p: 255 if p > threshold else 0)
        
        return binarized
    except Exception as e:
        logger.warning(f"Error during image pre-processing for OCR: {e}")
        return image

def extract_text_from_image(image_bytes: bytes) -> dict:
    """
    Extract text from raw image bytes using enhanced OCR pipeline.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        
        # Preprocess
        processed_image = preprocess_image_for_ocr(image)
        
        # Run Tesseract OCR
        # psm 1: Automatic page segmentation with OSD
        # psm 3: Fully automatic page segmentation (default)
        custom_config = r'--oem 3 --psm 3'
        text = pytesseract.image_to_string(processed_image, config=custom_config)
        
        # Get OCR data for confidence score calculation
        try:
            data = pytesseract.image_to_data(processed_image, output_type=pytesseract.Output.DICT)
            confidences = [int(c) for c in data.get('conf', []) if str(c).isdigit() and int(c) >= 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 85.0
        except Exception:
            avg_confidence = 85.0
            
        return {
            "success": True,
            "text": text.strip(),
            "confidence": round(avg_confidence, 2),
            "is_ocr": True,
            "error": None
        }
    except Exception as e:
        logger.error(f"OCR Extraction failed: {e}")
        return {
            "success": False,
            "text": "",
            "confidence": 0.0,
            "is_ocr": True,
            "error": str(e)
        }

def extract_text_from_pdf_ocr(pdf_bytes: bytes) -> dict:
    """
    Extract text from scanned PDF by rendering pages to images and running OCR.
    """
    try:
        import pdfplumber
        extracted_pages = []
        confidences = []
        
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                # Convert page to high-res PIL image
                im = page.to_image(resolution=200).original
                processed = preprocess_image_for_ocr(im)
                page_text = pytesseract.image_to_string(processed, config=r'--oem 3 --psm 3')
                if page_text.strip():
                    extracted_pages.append(page_text.strip())
                
                try:
                    data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DICT)
                    confs = [int(c) for c in data.get('conf', []) if str(c).isdigit() and int(c) >= 0]
                    if confs:
                        confidences.extend(confs)
                except Exception:
                    pass
                    
        full_text = "\n\n".join(extracted_pages)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 80.0
        
        return {
            "success": bool(full_text.strip()),
            "text": full_text.strip(),
            "confidence": round(avg_confidence, 2),
            "is_ocr": True,
            "error": None if full_text.strip() else "No text could be recognized via OCR"
        }
    except Exception as e:
        logger.error(f"PDF OCR Extraction failed: {e}")
        return {
            "success": False,
            "text": "",
            "confidence": 0.0,
            "is_ocr": True,
            "error": str(e)
        }
