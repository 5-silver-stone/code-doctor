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


MAX_FILES = 10
MAX_TOTAL_BYTES = 2 * 1024 * 1024


def validate_file_selection(files):
    """Check uploaded file count and cumulative size before reading the files."""
    if not isinstance(files, (list, tuple)):
        raise ValueError("파일 목록이 올바르지 않습니다.")
    if len(files) > MAX_FILES:
        raise ValueError(f"한 번에 최대 {MAX_FILES}개 파일까지 선택할 수 있습니다.")
    total = 0
    for item in files:
        size = getattr(item, "size", None)
        if not isinstance(size, int) or size < 0:
            raise ValueError("파일 크기를 확인할 수 없습니다.")
        if size > MAX_FILE_BYTES:
            raise ValueError(f"파일 1개당 최대 {MAX_FILE_BYTES // 1024}KB까지 지원합니다.")
        total += size
    if total > MAX_TOTAL_BYTES:
        raise ValueError("업로드한 파일의 전체 크기는 최대 2MB입니다.")
    return total
