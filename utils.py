from pdf2image import convert_from_bytes
import io


def pdf_to_image_bytes(pdf_bytes: bytes) -> bytes:
    images = convert_from_bytes(pdf_bytes)

    # İlk sayfayı al
    image = images[0]

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
