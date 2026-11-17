"""Validate and decode Python files pasted or uploaded through Streamlit.

No uploaded code is executed, imported, or sent to an external service.
"""
from pathlib import Path

MAX_FILE_BYTES = 512 * 1024


def decode_python_upload(filename, data, *, max_bytes=MAX_FILE_BYTES):
    """Return UTF-8 Python source text or raise a user-safe ValueError."""
    if not isinstance(filename, str) or Path(filename).suffix.lower() != ".py":
        raise ValueError("Python .py 파일만 업로드할 수 있습니다.")
    if not isinstance(data, (bytes, bytearray)):
        raise ValueError("파일 데이터를 읽을 수 없습니다.")
    if len(data) > max_bytes:
        raise ValueError(f"파일이 너무 큽니다. {max_bytes // 1024}KB 이하의 파일을 선택해 주세요.")
    try:
        return bytes(data).decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("UTF-8 인코딩된 Python 파일만 지원합니다.") from exc
