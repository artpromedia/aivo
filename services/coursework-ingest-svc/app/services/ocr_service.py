"""OCR processing service for extracting text from images and PDFs."""

import asyncio
import io
import logging
from typing import Any

try:
    import cv2
    import numpy as np
    import pytesseract
    from pdf2image import convert_from_bytes
    from PIL import Image, ImageEnhance
    OCR_DEPENDENCIES_AVAILABLE = True
    IMPORT_ERROR = ""
except ImportError as e:
    # Fallback if OCR dependencies are not available
    cv2 = None
    np = None
    pytesseract = None
    convert_from_bytes = None
    Image = None
    ImageEnhance = None
    OCR_DEPENDENCIES_AVAILABLE = False
    IMPORT_ERROR = str(e)

from app.config import settings

logger = logging.getLogger(__name__)


class OCRService:
    """Service for OCR text extraction."""

    def __init__(self) -> None:
        """Initialize OCR service."""
        if not OCR_DEPENDENCIES_AVAILABLE:
            error_msg = getattr(
                globals(), 'IMPORT_ERROR', 'Unknown import error'
            )
            logger.error(
                "OCR dependencies not available. Install: pip install "
                "opencv-python pytesseract pdf2image Pillow. Error: %s",
                error_msg
            )
            return

        if settings.tesseract_path and pytesseract:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_path

    async def extract_text_from_pdf(self, pdf_bytes: bytes) -> dict[str, Any]:
        """Extract text from PDF file."""
        if not OCR_DEPENDENCIES_AVAILABLE:
            raise ImportError("OCR dependencies not available")

        try:
            # Convert PDF to images
            images = await asyncio.to_thread(
                convert_from_bytes,
                pdf_bytes,
                dpi=300,
                poppler_path=settings.poppler_path,
            )

            all_text = []
            total_confidence = 0.0
            page_count = 0

            for i, image in enumerate(images):
                logger.info("Processing PDF page %d/%d", i + 1, len(images))

                # Preprocess image for better OCR
                preprocessed = await self._preprocess_image(image)

                # Extract text with confidence
                page_result = await asyncio.to_thread(
                    pytesseract.image_to_data,
                    preprocessed,
                    output_type=pytesseract.Output.DICT,
                    config="--psm 6",
                )

                # Filter out low-confidence text
                page_text = []
                page_confidences = []

                for j, conf in enumerate(page_result["conf"]):
                    if conf > 30:  # Minimum confidence threshold
                        text = page_result["text"][j].strip()
                        if text:
                            page_text.append(text)
                            page_confidences.append(conf)

                if page_text:
                    all_text.append(" ".join(page_text))
                    if page_confidences:
                        avg_page_conf = (
                            sum(page_confidences) / len(page_confidences)
                        )
                        total_confidence += avg_page_conf
                        page_count += 1

            extracted_text = "\n\n".join(all_text)
            if page_count > 0:
                average_confidence = total_confidence / page_count
            else:
                average_confidence = 0.0

            return {
                "text": extracted_text,
                "confidence": average_confidence / 100.0,  # Normalize to 0-1
                "pages_processed": len(images),
                "pages_with_text": page_count,
            }

        except Exception as e:
            logger.error("Error extracting text from PDF: %s", e)
            raise

    async def extract_text_from_image(
        self, image_bytes: bytes
    ) -> dict[str, Any]:
        """Extract text from image file."""
        if not OCR_DEPENDENCIES_AVAILABLE:
            raise ImportError("OCR dependencies not available")

        try:
            # Load image
            image = Image.open(io.BytesIO(image_bytes))

            # Convert to RGB if necessary
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Preprocess image for better OCR
            preprocessed = await self._preprocess_image(image)

            # Extract text with confidence
            result = await asyncio.to_thread(
                pytesseract.image_to_data,
                preprocessed,
                output_type=pytesseract.Output.DICT,
                config="--psm 6",
            )

            # Filter out low-confidence text
            extracted_words = []
            confidences = []

            for i, conf in enumerate(result["conf"]):
                if conf > 30:  # Minimum confidence threshold
                    text = result["text"][i].strip()
                    if text:
                        extracted_words.append(text)
                        confidences.append(conf)

            extracted_text = " ".join(extracted_words)
            if confidences:
                average_confidence = sum(confidences) / len(confidences)
            else:
                average_confidence = 0.0

            return {
                "text": extracted_text,
                "confidence": average_confidence / 100.0,  # Normalize to 0-1
                "words_extracted": len(extracted_words),
            }

        except Exception as e:
            logger.error("Error extracting text from image: %s", e)
            raise

    async def _preprocess_image(self, image: Any) -> Any:
        """Preprocess image for better OCR accuracy."""
        try:
            # Convert PIL Image to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            # Convert to grayscale
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

            # Apply noise reduction
            denoised = cv2.medianBlur(gray, 3)

            # Apply dilation and erosion to remove noise
            kernel = np.ones((1, 1), np.uint8)
            denoised = cv2.dilate(denoised, kernel, iterations=1)
            denoised = cv2.erode(denoised, kernel, iterations=1)

            # Apply Gaussian blur
            denoised = cv2.GaussianBlur(denoised, (5, 5), 0)

            # Apply thresholding to get binary image
            _, thresh = cv2.threshold(
                denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )

            # Convert back to PIL Image
            processed_image = Image.fromarray(thresh)

            # Enhance contrast
            enhancer = ImageEnhance.Contrast(processed_image)
            processed_image = enhancer.enhance(2.0)

            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(processed_image)
            processed_image = enhancer.enhance(1.5)

            return processed_image

        except (AttributeError, ValueError, OSError) as e:
            logger.warning("Error preprocessing image, using original: %s", e)
            return image

    async def extract_text(
        self, file_bytes: bytes, content_type: str
    ) -> dict[str, Any]:
        """Extract text from file based on content type."""
        if not OCR_DEPENDENCIES_AVAILABLE:
            raise ImportError("OCR dependencies not available")

        if content_type.lower() == "pdf":
            return await self.extract_text_from_pdf(file_bytes)
        else:
            return await self.extract_text_from_image(file_bytes)
