import mimetypes
import re
import uuid
from io import BytesIO
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from django.core.files.base import ContentFile
from django.utils.text import get_valid_filename
from PIL import Image


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".txt",
    ".log",
    ".zip",
    ".rar",
    ".7z",
}


def sanitize_filename(filename):
    """
    Return a safe display filename without path traversal.
    """

    filename = Path(filename).name
    filename = get_valid_filename(filename)

    if not filename:
        filename = "attachment"

    return filename


def generate_storage_name(filename):
    """
    Generate a non-predictable storage filename while preserving
    the processed file extension.
    """

    extension = Path(filename).suffix.lower()

    return f"{uuid.uuid4().hex}{extension}"


def _read_header(uploaded_file, size=8192):
    uploaded_file.seek(0)
    header = uploaded_file.read(size)
    uploaded_file.seek(0)

    return header


def validate_file_content(uploaded_file):
    """
    Validate the actual file content using signatures/basic parsers.
    """

    original_name = uploaded_file.name
    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("This file type is not supported.")

    header = _read_header(uploaded_file)

    # ---------------------------------------------------------
    # Images
    # ---------------------------------------------------------

    if extension in IMAGE_EXTENSIONS:
        try:
            image = Image.open(uploaded_file)
            image.verify()

        except Exception as exc:
            raise ValueError(
                "The uploaded image is invalid or corrupted."
            ) from exc

        finally:
            uploaded_file.seek(0)

        return

    # ---------------------------------------------------------
    # PDF
    # ---------------------------------------------------------

    if extension == ".pdf":
        if not header.startswith(b"%PDF-"):
            raise ValueError(
                "The uploaded PDF file is invalid."
            )

        return

    # ---------------------------------------------------------
    # Legacy Microsoft Office files
    # .doc / .xls / .ppt
    # ---------------------------------------------------------

    compound_file_signature = (
        b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
    )

    if extension in {".doc", ".xls", ".ppt"}:
        if not header.startswith(compound_file_signature):
            raise ValueError(
                "The uploaded Microsoft Office file is invalid."
            )

        return

    # ---------------------------------------------------------
    # Modern Microsoft Office files
    # .docx / .xlsx / .pptx
    # ---------------------------------------------------------

    if extension in {".docx", ".xlsx", ".pptx"}:
        try:
            with ZipFile(uploaded_file) as archive:
                names = set(archive.namelist())

                if "[Content_Types].xml" not in names:
                    raise ValueError(
                        "The uploaded Office document is invalid."
                    )

        except (BadZipFile, ValueError) as exc:
            raise ValueError(
                "The uploaded Office document is invalid or corrupted."
            ) from exc

        finally:
            uploaded_file.seek(0)

        return

    # ---------------------------------------------------------
    # ZIP
    # ---------------------------------------------------------

    if extension == ".zip":
        if not header.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
            raise ValueError(
                "The uploaded ZIP file is invalid."
            )

        try:
            with ZipFile(uploaded_file) as archive:
                archive.testzip()

        except BadZipFile as exc:
            raise ValueError(
                "The uploaded ZIP file is corrupted."
            ) from exc

        finally:
            uploaded_file.seek(0)

        return

    # ---------------------------------------------------------
    # RAR
    # ---------------------------------------------------------

    if extension == ".rar":
        rar_signature = (
            b"Rar!\x1a\x07"
        )

        if not header.startswith(rar_signature):
            raise ValueError(
                "The uploaded RAR file is invalid."
            )

        return

    # ---------------------------------------------------------
    # 7-Zip
    # ---------------------------------------------------------

    if extension == ".7z":
        seven_zip_signature = (
            b"\x37\x7a\xbc\xaf\x27\x1c"
        )

        if not header.startswith(seven_zip_signature):
            raise ValueError(
                "The uploaded 7-Zip file is invalid."
            )

        return

    # ---------------------------------------------------------
    # TXT / LOG
    # ---------------------------------------------------------

    if extension in {".txt", ".log"}:
        # Basic protection against files that are clearly binary.
        if b"\x00" in header:
            raise ValueError(
                "The uploaded text file appears to be binary."
            )

        return


def process_uploaded_file(uploaded_file):
    """
    Validate and process an uploaded file.

    Images are optimized while preserving good visual quality.
    Other supported file types are kept unchanged.
    """

    validate_file_content(uploaded_file)

    original_name = sanitize_filename(uploaded_file.name)
    extension = Path(original_name).suffix.lower()

    # Non-image files are kept unchanged.
    if extension not in IMAGE_EXTENSIONS:
        return uploaded_file, original_name

    try:
        uploaded_file.seek(0)

        image = Image.open(uploaded_file)

        output = BytesIO()

        if extension in {".jpg", ".jpeg"}:

            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")

            image.save(
                output,
                format="JPEG",
                quality=90,
                optimize=True,
                progressive=True,
            )

            processed_name = (
                f"{Path(original_name).stem}.jpg"
            )

        elif extension == ".png":

            image.save(
                output,
                format="PNG",
                optimize=True,
                compress_level=6,
            )

            processed_name = original_name

        elif extension == ".webp":

            image.save(
                output,
                format="WEBP",
                quality=90,
                method=6,
            )

            processed_name = original_name

        else:
            return uploaded_file, original_name

        output.seek(0)

        processed_file = ContentFile(
            output.read(),
            name=processed_name,
        )

        return processed_file, processed_name

    except Exception as exc:
        raise ValueError(
            "The uploaded image is invalid or corrupted."
        ) from exc

    finally:
        uploaded_file.seek(0)