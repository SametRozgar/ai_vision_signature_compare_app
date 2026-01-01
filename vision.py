import os
import os
from dotenv import load_dotenv

load_dotenv()  
import io
import base64
from typing import Tuple

from openai import OpenAI
from pdf2image import convert_from_bytes
from PIL import Image


# --------------------------------------------------
# OpenAI Client
# --------------------------------------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# --------------------------------------------------
# Utils
# --------------------------------------------------
def is_pdf(file_bytes: bytes) -> bool:
    return file_bytes[:4] == b"%PDF"


def pdf_bytes_to_png_bytes(pdf_bytes: bytes) -> bytes:
    """
    Converts first page of PDF to PNG bytes
    """
    images = convert_from_bytes(pdf_bytes)
    first_page: Image.Image = images[0]

    buffer = io.BytesIO()
    first_page.save(buffer, format="PNG")
    return buffer.getvalue()


def image_bytes_to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def normalize_to_png_bytes(file_bytes: bytes) -> bytes:
    """
    Accepts PDF or image bytes
    Returns PNG bytes
    """
    if is_pdf(file_bytes):
        return pdf_bytes_to_png_bytes(file_bytes)

    # image → normalize to PNG
    image = Image.open(io.BytesIO(file_bytes))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


# --------------------------------------------------
# MAIN LOGIC
# --------------------------------------------------
def compare_signatures(
    passport_bytes: bytes,
    signed_document_bytes: bytes
) -> dict:
    """
    Compares signatures between passport and signed document.

    Returns:
    {
        "has_signature": bool,
        "similarity_percent": int,
        "message": str
    }
    """

    # Normalize inputs
    passport_png = normalize_to_png_bytes(passport_bytes)
    signed_png = normalize_to_png_bytes(signed_document_bytes)

    passport_b64 = image_bytes_to_base64(passport_png)
    signed_b64 = image_bytes_to_base64(signed_png)

    prompt = """
You are a document verification AI.

Tasks:
1. Check if the signed document actually contains a handwritten signature.
2. If there is NO signature, respond clearly.
3. If there IS a signature, compare it with the passport signature.
4. Estimate similarity percentage between 0 and 100.

Rules:
- If no signature exists, similarity must be 0.
- Be conservative.
- Respond ONLY in valid JSON format.

Expected JSON:
{
  "has_signature": true/false,
  "similarity_percent": number,
  "message": "string"
}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{passport_b64}"
                        }
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{signed_b64}"
                        }
                    }
                ]
            }
        ],
        max_tokens=300
    )

    raw = response.choices[0].message.content

    # Fallback protection
    try:
        import json
        return json.loads(raw)
    except Exception:
        return {
            "has_signature": False,
            "similarity_percent": 0,
            "message": raw
        }
