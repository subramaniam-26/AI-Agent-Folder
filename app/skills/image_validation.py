from app.security import log_audit

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

def _get_extension(filename: str) -> str:
    return filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

def validate_image_file(filename: str, file_content: bytes) -> dict:
    """Validate image file for soil analysis.

    Parameters:
        filename: Name of the uploaded file.
        file_content: Raw bytes of the file.

    Returns:
        dict with keys:
            "valid": bool - whether the file passes all checks.
            "reason": str - explanation if invalid.
    """
    # 1. Extension check
    ext = _get_extension(filename)
    if ext not in ALLOWED_EXTENSIONS:
        reason = f"Unsupported file extension '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
        log_audit("image_validation", "REJECT", reason)
        return {"valid": False, "reason": reason}

    # 2. Size check
    if len(file_content) > MAX_SIZE_BYTES:
        reason = f"File size {len(file_content)} exceeds maximum of {MAX_SIZE_BYTES} bytes."
        log_audit("image_validation", "REJECT", reason)
        return {"valid": False, "reason": reason}

    # 3. Basic visibility check - placeholder (real check would involve ML)
    # For now we only accept non-empty content as a minimal sanity check.
    if not file_content:
        reason = "Empty file content."
        log_audit("image_validation", "REJECT", reason)
        return {"valid": False, "reason": reason}

    # Passed all checks
    log_audit("image_validation", "PASS", f"File '{filename}' passed validation.")
    return {"valid": True, "reason": ""}
