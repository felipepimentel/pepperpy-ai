"""Advanced OCR for document processing.

This module provides advanced OCR functionality with multi-language support
for extracting text from images and document scans.
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pepperpy.core.base import PepperpyError

logger = logging.getLogger(__name__)

# Try to import OCR libraries
try:
    import pytesseract

    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pdf2image

    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

try:
    import cv2

    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

try:
    import easyocr

    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False


class OCRError(PepperpyError):
    """Error raised during OCR operations."""

    pass


class OCRProcessor:
    """Processor for advanced Optical Character Recognition.

    This class provides functionality for extracting text from images and document
    scans using OCR, with support for multiple languages and OCR engines.
    """

    # Default OCR engine
    DEFAULT_ENGINE = "tesseract"

    # Supported OCR engines
    SUPPORTED_ENGINES = {
        "tesseract": TESSERACT_AVAILABLE,
        "easyocr": EASYOCR_AVAILABLE,
    }

    # Supported image formats
    SUPPORTED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".gif"}

    # Default preprocessing options
    DEFAULT_PREPROCESSING = {
        "resize": False,
        "resize_width": 1800,
        "denoise": False,
        "deskew": False,
        "contrast": False,
        "threshold": False,
    }

    # Default language
    DEFAULT_LANGUAGE = "eng"

    # Available languages by engine
    # This is not a comprehensive list, just the most common languages
    AVAILABLE_LANGUAGES = {
        "tesseract": {
            "afr": "Afrikaans",
            "amh": "Amharic",
            "ara": "Arabic",
            "asm": "Assamese",
            "aze": "Azerbaijani",
            "bel": "Belarusian",
            "ben": "Bengali",
            "bod": "Tibetan",
            "bos": "Bosnian",
            "bul": "Bulgarian",
            "cat": "Catalan",
            "ceb": "Cebuano",
            "ces": "Czech",
            "chi_sim": "Chinese (Simplified)",
            "chi_tra": "Chinese (Traditional)",
            "chr": "Cherokee",
            "cym": "Welsh",
            "dan": "Danish",
            "deu": "German",
            "dzo": "Dzongkha",
            "ell": "Greek",
            "eng": "English",
            "enm": "English (Middle)",
            "epo": "Esperanto",
            "est": "Estonian",
            "eus": "Basque",
            "fas": "Persian",
            "fin": "Finnish",
            "fra": "French",
            "frk": "Frankish",
            "frm": "French (Middle)",
            "gle": "Irish",
            "glg": "Galician",
            "grc": "Greek (Ancient)",
            "guj": "Gujarati",
            "hat": "Haitian",
            "heb": "Hebrew",
            "hin": "Hindi",
            "hrv": "Croatian",
            "hun": "Hungarian",
            "iku": "Inuktitut",
            "ind": "Indonesian",
            "isl": "Icelandic",
            "ita": "Italian",
            "jav": "Javanese",
            "jpn": "Japanese",
            "kan": "Kannada",
            "kat": "Georgian",
            "kaz": "Kazakh",
            "khm": "Khmer",
            "kir": "Kyrgyz",
            "kor": "Korean",
            "kur": "Kurdish",
            "lao": "Lao",
            "lat": "Latin",
            "lav": "Latvian",
            "lit": "Lithuanian",
            "mal": "Malayalam",
            "mar": "Marathi",
            "mkd": "Macedonian",
            "mlt": "Maltese",
            "msa": "Malay",
            "mya": "Burmese",
            "nep": "Nepali",
            "nld": "Dutch",
            "nor": "Norwegian",
            "ori": "Oriya",
            "pan": "Punjabi",
            "pol": "Polish",
            "por": "Portuguese",
            "pus": "Pashto",
            "ron": "Romanian",
            "rus": "Russian",
            "san": "Sanskrit",
            "sin": "Sinhala",
            "slk": "Slovak",
            "slv": "Slovenian",
            "spa": "Spanish",
            "sqi": "Albanian",
            "srp": "Serbian",
            "swa": "Swahili",
            "swe": "Swedish",
            "syr": "Syriac",
            "tam": "Tamil",
            "tel": "Telugu",
            "tgk": "Tajik",
            "tgl": "Tagalog",
            "tha": "Thai",
            "tir": "Tigrinya",
            "tur": "Turkish",
            "uig": "Uyghur",
            "ukr": "Ukrainian",
            "urd": "Urdu",
            "uzb": "Uzbek",
            "vie": "Vietnamese",
            "yid": "Yiddish",
        },
        "easyocr": {
            "abq": "Abaza",
            "ady": "Adyghe",
            "af": "Afrikaans",
            "ang": "English (Old)",
            "ar": "Arabic",
            "as": "Assamese",
            "ava": "Avar",
            "az": "Azerbaijani",
            "be": "Belarusian",
            "bg": "Bulgarian",
            "bh": "Bihari",
            "bn": "Bengali",
            "bs": "Bosnian",
            "ch_sim": "Chinese (Simplified)",
            "ch_tra": "Chinese (Traditional)",
            "che": "Chechen",
            "cs": "Czech",
            "cy": "Welsh",
            "da": "Danish",
            "dar": "Dargwa",
            "de": "German",
            "el": "Greek",
            "en": "English",
            "es": "Spanish",
            "et": "Estonian",
            "fa": "Persian",
            "fi": "Finnish",
            "fr": "French",
            "ga": "Irish",
            "gom": "Goan Konkani",
            "hi": "Hindi",
            "hr": "Croatian",
            "hu": "Hungarian",
            "id": "Indonesian",
            "inh": "Ingush",
            "is": "Icelandic",
            "it": "Italian",
            "ja": "Japanese",
            "ka": "Georgian",
            "kk": "Kazakh",
            "km": "Khmer",
            "kn": "Kannada",
            "ko": "Korean",
            "ku": "Kurdish",
            "la": "Latin",
            "lbe": "Lak",
            "lez": "Lezghian",
            "lt": "Lithuanian",
            "lv": "Latvian",
            "mhr": "Eastern Mari",
            "mi": "Maori",
            "mn": "Mongolian",
            "mr": "Marathi",
            "ms": "Malay",
            "mt": "Maltese",
            "ne": "Nepali",
            "nl": "Dutch",
            "no": "Norwegian",
            "oc": "Occitan",
            "pi": "Pali",
            "pl": "Polish",
            "pt": "Portuguese",
            "ro": "Romanian",
            "ru": "Russian",
            "rs_cyrillic": "Serbian (Cyrillic)",
            "rs_latin": "Serbian (Latin)",
            "sa": "Sanskrit",
            "si": "Sinhala",
            "sk": "Slovak",
            "sl": "Slovenian",
            "sq": "Albanian",
            "sv": "Swedish",
            "sw": "Swahili",
            "ta": "Tamil",
            "tab": "Tabassaran",
            "te": "Telugu",
            "th": "Thai",
            "tjk": "Tajik",
            "tl": "Tagalog",
            "tr": "Turkish",
            "ug": "Uyghur",
            "uk": "Ukrainian",
            "ur": "Urdu",
            "uz": "Uzbek",
            "vi": "Vietnamese",
        },
    }

    # Language code mappings between engines
    LANGUAGE_CODE_MAPPINGS = {
        "tesseract_to_easyocr": {
            "ara": "ar",
            "aze": "az",
            "bel": "be",
            "ben": "bn",
            "bul": "bg",
            "cat": "ca",
            "ces": "cs",
            "chi_sim": "ch_sim",
            "chi_tra": "ch_tra",
            "cym": "cy",
            "dan": "da",
            "deu": "de",
            "ell": "el",
            "eng": "en",
            "est": "et",
            "eus": "eu",
            "fas": "fa",
            "fin": "fi",
            "fra": "fr",
            "gle": "ga",
            "glg": "gl",
            "guj": "gu",
            "heb": "he",
            "hin": "hi",
            "hrv": "hr",
            "hun": "hu",
            "ind": "id",
            "isl": "is",
            "ita": "it",
            "jpn": "ja",
            "kan": "kn",
            "kat": "ka",
            "kaz": "kk",
            "khm": "km",
            "kor": "ko",
            "kur": "ku",
            "lat": "la",
            "lav": "lv",
            "lit": "lt",
            "mal": "ml",
            "mar": "mr",
            "mkd": "mk",
            "mlt": "mt",
            "msa": "ms",
            "nep": "ne",
            "nld": "nl",
            "nor": "no",
            "pol": "pl",
            "por": "pt",
            "ron": "ro",
            "rus": "ru",
            "slk": "sk",
            "slv": "sl",
            "spa": "es",
            "sqi": "sq",
            "srp": "rs_cyrillic",
            "swa": "sw",
            "swe": "sv",
            "tam": "ta",
            "tel": "te",
            "tha": "th",
            "tur": "tr",
            "ukr": "uk",
            "urd": "ur",
            "uzb": "uz",
            "vie": "vi",
        },
        "easyocr_to_tesseract": {
            "ar": "ara",
            "az": "aze",
            "be": "bel",
            "bn": "ben",
            "bg": "bul",
            "ca": "cat",
            "cs": "ces",
            "ch_sim": "chi_sim",
            "ch_tra": "chi_tra",
            "cy": "cym",
            "da": "dan",
            "de": "deu",
            "el": "ell",
            "en": "eng",
            "et": "est",
            "eu": "eus",
            "fa": "fas",
            "fi": "fin",
            "fr": "fra",
            "ga": "gle",
            "gl": "glg",
            "gu": "guj",
            "he": "heb",
            "hi": "hin",
            "hr": "hrv",
            "hu": "hun",
            "id": "ind",
            "is": "isl",
            "it": "ita",
            "ja": "jpn",
            "kn": "kan",
            "ka": "kat",
            "kk": "kaz",
            "km": "khm",
            "ko": "kor",
            "ku": "kur",
            "la": "lat",
            "lv": "lav",
            "lt": "lit",
            "ml": "mal",
            "mr": "mar",
            "mk": "mkd",
            "mt": "mlt",
            "ms": "msa",
            "ne": "nep",
            "nl": "nld",
            "no": "nor",
            "pl": "pol",
            "pt": "por",
            "ro": "ron",
            "ru": "rus",
            "sk": "slk",
            "sl": "slv",
            "es": "spa",
            "sq": "sqi",
            "rs_cyrillic": "srp",
            "sw": "swa",
            "sv": "swe",
            "ta": "tam",
            "te": "tel",
            "th": "tha",
            "tr": "tur",
            "uk": "ukr",
            "ur": "urd",
            "uz": "uzb",
            "vi": "vie",
        },
    }

    def __init__(
        self,
        engine: str = DEFAULT_ENGINE,
        languages: Optional[List[str]] = None,
        preprocessing: Optional[Dict[str, Any]] = None,
        temp_dir: Optional[Union[str, Path]] = None,
        tesseract_cmd: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize OCR processor.

        Args:
            engine: OCR engine to use
            languages: List of language codes
            preprocessing: Preprocessing options
            temp_dir: Temporary directory for processed files
            tesseract_cmd: Path to tesseract command (for tesseract engine)
            **kwargs: Additional configuration options
        """
        # Check required dependencies
        if not PIL_AVAILABLE:
            raise OCRError("PIL is required for OCR processing")

        # Set engine
        if engine not in self.SUPPORTED_ENGINES:
            raise OCRError(f"Unsupported OCR engine: {engine}")

        if not self.SUPPORTED_ENGINES[engine]:
            raise OCRError(f"OCR engine {engine} is not available")

        self.engine = engine

        # Set languages
        self.languages = languages or [self.DEFAULT_LANGUAGE]

        # Validate languages
        if engine == "tesseract":
            for lang in self.languages:
                if lang not in self.AVAILABLE_LANGUAGES["tesseract"]:
                    logger.warning(
                        f"Language {lang} is not in the known language list for tesseract"
                    )
        elif engine == "easyocr":
            for lang in self.languages:
                if lang not in self.AVAILABLE_LANGUAGES["easyocr"]:
                    logger.warning(
                        f"Language {lang} is not in the known language list for easyocr"
                    )

        # Set preprocessing options
        self.preprocessing = self.DEFAULT_PREPROCESSING.copy()
        if preprocessing:
            self.preprocessing.update(preprocessing)

        # Set temporary directory
        if temp_dir is None:
            self.temp_dir = Path(tempfile.gettempdir()) / "pepperpy" / "ocr"
        elif isinstance(temp_dir, str):
            self.temp_dir = Path(temp_dir)
        else:
            self.temp_dir = temp_dir

        # Create temp directory if it doesn't exist
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Set tesseract command path
        if tesseract_cmd and engine == "tesseract":
            if pytesseract:
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

        # Initialize OCR engine
        self._initialize_engine(**kwargs)

    def _initialize_engine(self, **kwargs: Any) -> None:
        """Initialize OCR engine."""
        if self.engine == "easyocr":
            # Initialize EasyOCR reader
            self.reader = easyocr.Reader(
                lang_list=self.languages,
                gpu=kwargs.get("gpu", True),
                model_storage_directory=str(self.temp_dir / "models"),
                download_enabled=kwargs.get("download_enabled", True),
                detector=kwargs.get("detector", True),
                recognizer=kwargs.get("recognizer", True),
                quantize=kwargs.get("quantize", True),
                cudnn_benchmark=kwargs.get("cudnn_benchmark", False),
            )
        elif self.engine == "tesseract":
            # No initialization needed for tesseract
            pass

    def is_supported_image(self, file_path: Union[str, Path]) -> bool:
        """Check if a file is a supported image format.

        Args:
            file_path: Path to file

        Returns:
            True if file is a supported image format
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        # Check if file exists
        if not file_path.exists():
            return False

        # Check file extension
        return file_path.suffix.lower() in self.SUPPORTED_IMAGE_FORMATS

    def preprocess_image(
        self,
        image: Union[str, Path, Image.Image],
        output_path: Optional[Union[str, Path]] = None,
    ) -> Image.Image:
        """Preprocess image for OCR.

        Args:
            image: Path to image or PIL Image object
            output_path: Path to save preprocessed image (optional)

        Returns:
            Preprocessed PIL Image
        """
        # Load image if path provided
        if isinstance(image, (str, Path)):
            image = Image.open(image)

        # Convert to OpenCV format for preprocessing
        if OPENCV_AVAILABLE and any(self.preprocessing.values()):
            import numpy as np

            # Convert PIL image to OpenCV format
            img_np = np.array(image)

            # Convert to grayscale if not already
            if len(img_np.shape) == 3:
                gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_np

            # Resize to improve OCR
            if self.preprocessing["resize"]:
                height, width = gray.shape
                if width > self.preprocessing["resize_width"]:
                    ratio = self.preprocessing["resize_width"] / width
                    new_height = int(height * ratio)
                    gray = cv2.resize(
                        gray, (self.preprocessing["resize_width"], new_height)
                    )

            # Apply thresholding to improve contrast
            if self.preprocessing["threshold"]:
                gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[
                    1
                ]

            # Apply contrast enhancement
            if self.preprocessing["contrast"]:
                gray = cv2.equalizeHist(gray)

            # Apply denoising
            if self.preprocessing["denoise"]:
                gray = cv2.GaussianBlur(gray, (5, 5), 0)

            # Apply deskewing
            if self.preprocessing["deskew"]:
                coords = np.column_stack(np.where(gray > 0))
                angle = cv2.minAreaRect(coords)[-1]
                if angle < -45:
                    angle = -(90 + angle)
                else:
                    angle = -angle

                # Rotate the image to deskew it
                (h, w) = gray.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                rotated = cv2.warpAffine(
                    gray,
                    M,
                    (w, h),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE,
                )
                gray = rotated

            # Convert back to PIL image
            processed_image = Image.fromarray(gray)
        else:
            processed_image = image

        # Save preprocessed image if output path provided
        if output_path:
            if isinstance(output_path, str):
                output_path = Path(output_path)

            processed_image.save(output_path)

        return processed_image

    def extract_text_from_image(
        self, image: Union[str, Path, Image.Image], **kwargs: Any
    ) -> str:
        """Extract text from image using OCR.

        Args:
            image: Path to image or PIL Image object
            **kwargs: Additional engine-specific parameters

        Returns:
            Extracted text

        Raises:
            OCRError: If text extraction fails
        """
        try:
            # Load and preprocess image
            if isinstance(image, (str, Path)):
                if not Path(image).exists():
                    raise OCRError(f"Image file not found: {image}")

                # Preprocess image
                processed_image = self.preprocess_image(image)
            else:
                # Preprocess image
                processed_image = self.preprocess_image(image)

            # Extract text using selected engine
            if self.engine == "tesseract":
                return self._extract_text_tesseract(processed_image, **kwargs)
            elif self.engine == "easyocr":
                return self._extract_text_easyocr(processed_image, **kwargs)
            else:
                raise OCRError(f"Unsupported OCR engine: {self.engine}")
        except Exception as e:
            raise OCRError(f"Error extracting text from image: {e}")

    def _extract_text_tesseract(self, image: Image.Image, **kwargs: Any) -> str:
        """Extract text using Tesseract OCR.

        Args:
            image: PIL Image object
            **kwargs: Additional tesseract-specific parameters

        Returns:
            Extracted text
        """
        # Set tesseract configuration
        config = kwargs.get("config", "")

        # Set language
        lang = "+".join(self.languages)

        # Extract text
        text = pytesseract.image_to_string(image, lang=lang, config=config)

        return text

    def _extract_text_easyocr(self, image: Image.Image, **kwargs: Any) -> str:
        """Extract text using EasyOCR.

        Args:
            image: PIL Image object
            **kwargs: Additional easyocr-specific parameters

        Returns:
            Extracted text
        """
        # Set EasyOCR parameters
        detail = kwargs.get("detail", 0)
        paragraph = kwargs.get("paragraph", True)

        # Convert PIL image to OpenCV format
        import numpy as np

        img_np = np.array(image)

        # Extract text
        result = self.reader.readtext(img_np, detail=detail, paragraph=paragraph)

        # Extract text from result
        if detail == 0 and not paragraph:
            # Result is a list of strings
            return "\n".join(result)
        elif detail == 0 and paragraph:
            # Result is a single string
            return result
        else:
            # Result is a list of tuples with bounding boxes and text
            return "\n".join([detection[1] for detection in result])

    def extract_text_from_pdf(
        self,
        pdf_path: Union[str, Path],
        start_page: int = 0,
        end_page: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """Extract text from PDF using OCR.

        Args:
            pdf_path: Path to PDF file
            start_page: First page to process (0-based)
            end_page: Last page to process (0-based, None for all pages)
            **kwargs: Additional engine-specific parameters

        Returns:
            Extracted text

        Raises:
            OCRError: If text extraction fails
        """
        if not PDF2IMAGE_AVAILABLE:
            raise OCRError("pdf2image is required for PDF OCR processing")

        try:
            # Convert PDF to images
            images = pdf2image.convert_from_path(
                pdf_path,
                first_page=start_page + 1,  # pdf2image uses 1-based indexing
                last_page=None if end_page is None else end_page + 1,
                dpi=kwargs.get("dpi", 300),
                thread_count=kwargs.get("thread_count", 1),
                grayscale=kwargs.get("grayscale", True),
            )

            # Extract text from each image
            all_text = []
            for i, img in enumerate(images):
                page_num = start_page + i
                logger.debug(f"Processing page {page_num} of {pdf_path}")

                # Extract text
                text = self.extract_text_from_image(img, **kwargs)

                # Add page information and text
                all_text.append(f"--- Page {page_num + 1} ---\n{text}")

            return "\n\n".join(all_text)
        except Exception as e:
            raise OCRError(f"Error extracting text from PDF: {e}")

    def extract_tables_from_image(
        self, image: Union[str, Path, Image.Image], **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """Extract tables from image.

        Args:
            image: Path to image or PIL Image object
            **kwargs: Additional engine-specific parameters

        Returns:
            List of extracted tables

        Raises:
            OCRError: If table extraction fails
        """
        # Currently only implemented for OpenCV
        if not OPENCV_AVAILABLE:
            raise OCRError("OpenCV is required for table extraction")

        try:
            # Load and preprocess image
            if isinstance(image, (str, Path)):
                if not Path(image).exists():
                    raise OCRError(f"Image file not found: {image}")

                # Load image with OpenCV
                img = cv2.imread(str(image))
            else:
                # Convert PIL image to OpenCV format
                import numpy as np

                img = np.array(image)
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Threshold
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
            )

            # Find contours
            contours, _ = cv2.findContours(
                thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            # Filter contours by size
            min_area = kwargs.get("min_area", 100)
            max_area = kwargs.get("max_area", img.shape[0] * img.shape[1] * 0.5)
            contours = [c for c in contours if min_area < cv2.contourArea(c) < max_area]

            # Sort contours by position (top to bottom)
            contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[1])

            # Extract tables
            tables = []
            for i, contour in enumerate(contours):
                # Get bounding box
                x, y, w, h = cv2.boundingRect(contour)

                # Extract region
                region = img[y : y + h, x : x + w]

                # Create temporary file for the region
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp:
                    temp_path = temp.name

                # Save region to temp file
                cv2.imwrite(temp_path, region)

                # Extract text from region
                text = self.extract_text_from_image(temp_path, **kwargs)

                # Parse table
                # This is a basic implementation that treats each line as a row
                # More sophisticated table parsing would require additional logic
                rows = [line.strip() for line in text.split("\n") if line.strip()]

                # Add table to results
                tables.append({
                    "id": i,
                    "position": {"x": x, "y": y, "width": w, "height": h},
                    "text": text,
                    "rows": rows,
                })

                # Clean up temp file
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

            return tables
        except Exception as e:
            raise OCRError(f"Error extracting tables from image: {e}")

    def clean_temp_files(self) -> int:
        """Clean up temporary files.

        Returns:
            Number of files deleted
        """
        count = 0
        for path in self.temp_dir.glob("**/*"):
            if path.is_file():
                try:
                    path.unlink()
                    count += 1
                except OSError:
                    # Ignore errors
                    pass

        # Remove empty directories
        for path in sorted(
            self.temp_dir.glob("**/*"), key=lambda p: str(p), reverse=True
        ):
            if path.is_dir():
                try:
                    path.rmdir()
                except OSError:
                    # Directory not empty or other error
                    pass

        return count

    def get_available_languages(self, engine: Optional[str] = None) -> Dict[str, str]:
        """Get available languages for OCR engine.

        Args:
            engine: OCR engine name (if None, use current engine)

        Returns:
            Dictionary of language code to language name
        """
        engine = engine or self.engine

        if engine not in self.AVAILABLE_LANGUAGES:
            logger.warning(f"Unknown OCR engine: {engine}")
            return {}

        return self.AVAILABLE_LANGUAGES[engine]

    def convert_language_code(
        self, code: str, source_engine: str, target_engine: str
    ) -> Optional[str]:
        """Convert language code between engines.

        Args:
            code: Language code to convert
            source_engine: Source OCR engine
            target_engine: Target OCR engine

        Returns:
            Converted language code or None if not found
        """
        if source_engine == target_engine:
            return code

        # Get conversion map key
        map_key = f"{source_engine}_to_{target_engine}"

        # Check if conversion map exists
        if map_key not in self.LANGUAGE_CODE_MAPPINGS:
            logger.warning(
                f"No language code mapping from {source_engine} to {target_engine}"
            )
            return None

        # Get conversion map
        code_map = self.LANGUAGE_CODE_MAPPINGS[map_key]

        # Convert code
        return code_map.get(code)


# Global OCR processor instance
_ocr_processor: Optional[OCRProcessor] = None


def get_ocr_processor(
    engine: str = OCRProcessor.DEFAULT_ENGINE,
    languages: Optional[List[str]] = None,
    preprocessing: Optional[Dict[str, Any]] = None,
    temp_dir: Optional[Union[str, Path]] = None,
    tesseract_cmd: Optional[str] = None,
    **kwargs: Any,
) -> OCRProcessor:
    """Get OCR processor instance.

    Args:
        engine: OCR engine to use
        languages: List of language codes
        preprocessing: Preprocessing options
        temp_dir: Temporary directory for processed files
        tesseract_cmd: Path to tesseract command (for tesseract engine)
        **kwargs: Additional configuration options

    Returns:
        OCR processor instance
    """
    global _ocr_processor

    # Always create a new instance if parameters change
    if (
        _ocr_processor is None
        or _ocr_processor.engine != engine
        or (languages is not None and _ocr_processor.languages != languages)
    ):
        _ocr_processor = OCRProcessor(
            engine=engine,
            languages=languages,
            preprocessing=preprocessing,
            temp_dir=temp_dir,
            tesseract_cmd=tesseract_cmd,
            **kwargs,
        )

    return _ocr_processor
