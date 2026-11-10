"""Non-executing Python syntax checks and local error-type explanations."""
import ast
import re

ERROR_DESCRIPTIONS = {
    "SyntaxError": "Python 문법이 올바르지 않습니다. 콜론, 괄호, 따옴표 등을 확인하세요.",
    "IndentationError": "들여쓰기 위치나 공백 개수가 잘못되었을 수 있습니다.",
    "NameError": "정의되지 않은 변수나 함수를 사용했을 수 있습니다. 오타와 선언 순서를 확인하세요.",
    "TypeError": "지원되지 않는 자료형 조합이나 함수 인자 사용을 확인하세요.",
    "ValueError": "자료형은 맞지만 함수가 허용하지 않는 값을 전달했을 수 있습니다.",
    "KeyError": "딕셔너리에 없는 키로 값을 찾으려 했을 수 있습니다.",
    "IndexError": "리스트 등에서 유효 범위를 벗어난 인덱스를 사용했을 수 있습니다.",
    "AttributeError": "해당 객체에 없는 속성이나 메서드를 호출했을 수 있습니다.",
    "ModuleNotFoundError": "모듈이 설치되지 않았거나 현재 Python 환경에서 찾지 못하는 경우입니다.",
    "ImportError": "모듈이나 이름을 가져올 수 없습니다. 설치, 이름, 버전 등을 확인하세요.",
    "ZeroDivisionError": "0으로 나누는 연산을 수행했을 수 있습니다.",
    "FileNotFoundError": "지정한 파일이나 경로가 존재하지 않을 수 있습니다.",
    "StreamlitDuplicateElementKey": "Streamlit 위젯들의 key가 중복되지 않는지 확인하세요.",
    "StreamlitDuplicateElementId": "Streamlit이 동일한 위젯 ID를 생성했을 수 있습니다. 위젯에 고유 key를 부여하세요.",
}


def classify_error(message):
    for error_type in sorted(ERROR_DESCRIPTIONS, key=len, reverse=True):
        if re.search(r"\b" + re.escape(error_type) + r"\b", message or ""):
            return error_type, ERROR_DESCRIPTIONS[error_type]
    match = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*(?:Error|Exception))\b", message or "")
    if match:
        return match.group(1), "이 오류의 정확한 원인은 실행 환경과 코드에 따라 달라질 수 있습니다."
    return "", "오류 이름을 추출하지 못했습니다. 오류 메시지 또는 검색 키워드를 입력하세요."


def check_python(code):
    if not code.strip():
        return {"checked": False, "passed": False, "message": "검사할 코드가 없습니다."}
    try:
        ast.parse(code)
        return {"checked": True, "passed": True,
                "message": "Python 문법 검사를 통과했습니다. 실제 실행 및 논리적 정확성은 확인하지 않았습니다."}
    except SyntaxError as exc:
        return {"checked": True, "passed": False, "message": exc.msg,
                "line": exc.lineno, "column": exc.offset, "error_type": type(exc).__name__}


def suggest_query(message, language="python"):
    """Send only a minimal search query. Never transmit pasted code or full traceback."""
    category, _ = classify_error(message)
    lines = (message or "").splitlines()
    if category:
        for line in reversed(lines):
            if category in line:
                tail = line.split(category, 1)[-1].lstrip(": ")
                # Keep a short diagnostic without local paths, emails, or quoted secrets.
                tail = re.sub(r"(['\"]).*?\1", "", tail)
                tail = re.sub(r"(?:[A-Za-z]:)?[/\\][\w./\\-]+", "", tail)
                tail = re.sub(r"\b\S+@\S+\b", "", tail)
                tail = re.sub(r"\s+", " ", tail).strip()[:90]
                return f"{category} {tail}".strip()
        return category
    # Unknown messages are not automatically transmitted; user enters own search keyword.
    return ""


def extract_missing_module(message):
    if "ModuleNotFoundError" not in (message or ""):
        return ""
    match = re.search(r"No module named ['\"]([a-zA-Z0-9_.-]+)['\"]", message)
    return match.group(1).split(".")[0] if match else ""
