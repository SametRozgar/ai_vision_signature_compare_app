from fastapi import FastAPI, UploadFile, File
import json
from vision import compare_signatures

app = FastAPI()


@app.post("/verify-signature")
async def verify_signature(
    passport: UploadFile = File(...),
    signed_document: UploadFile = File(...)
):
    passport_bytes = await passport.read()
    signed_bytes = await signed_document.read()

    ai_result = compare_signatures(passport_bytes, signed_bytes)

    try:
        result = json.loads(ai_result)
    except Exception:
        return {
            "has_signature": False,
            "similarity_percent": 0,
            "message": "AI response could not be parsed"
        }

    has_signature = result.get("has_signature", False)
    similarity = result.get("similarity_percent", 0)

    if not has_signature:
        return {
            "has_signature": False,
            "similarity_percent": 0,
            "message": "There is no signature"
        }

    if similarity < 60:
        return {
            "has_signature": True,
            "similarity_percent": similarity,
            "message": "Signatures are very different"
        }

    return {
        "has_signature": True,
        "similarity_percent": similarity,
        "message": "Signatures are similar"
    }
