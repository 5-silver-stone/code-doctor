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
    "UnboundLocalError": "지역 변수를 값이 할당되기 전에 사용했을 수 있습니다. 초기화 위치와 변수 범위를 확인하세요.",
    "PermissionError": "파일 또는 폴더에 접근 권한이 없을 수 있습니다. 권한과 경로를 확인하세요.",
    "FileExistsError": "만들려는 파일 또는 폴더가 이미 존재할 수 있습니다.",
    "IsADirectoryError": "파일이 필요한 위치에 폴더 경로를 입력했을 수 있습니다.",
    "NotADirectoryError": "폴더가 필요한 위치에 파일 경로를 입력했을 수 있습니다.",
    "UnicodeDecodeError": "텍스트 파일의 인코딩이 예상과 다를 수 있습니다. UTF-8 등 인코딩을 확인하세요.",
    "JSONDecodeError": "JSON 문자열이 올바른 형식이 아닌 경우입니다. 따옴표와 쉼표를 확인하세요.",
    "RuntimeError": "프로그램 실행 과정에서 발생한 오류입니다. 오류 메시지와 호출 위치를 확인하세요.",
    "AssertionError": "assert 조건이 거짓이었습니다. 예상 조건과 실제 값을 비교하세요.",
    "RecursionError": "함수가 너무 깊게 재귀 호출되었습니다. 종료 조건을 확인하세요.",
    "MemoryError": "작업에 필요한 메모리를 확보하지 못했습니다. 입력 크기와 데이터 처리 방식을 확인하세요.",
    "TimeoutError": "작업이 허용 시간 안에 끝나지 않았습니다. 처리 시간이나 연결 상태를 확인하세요.",
    "ConnectionError": "네트워크 연결에 문제가 있을 수 있습니다. 주소와 연결 상태를 확인하세요.",
    "OSError": "운영체제에서 작업을 처리하지 못했습니다. 경로와 권한, 파일 상태 등을 확인하세요.",
    "StreamlitAPIException": "Streamlit API 사용 방식이나 위젯 인자를 확인하세요.",
}


ERROR_GROUPS = {
    "문법·들여쓰기": {"SyntaxError", "IndentationError"},
    "변수·자료형": {"NameError", "UnboundLocalError", "TypeError", "AttributeError"},
    "자료·값": {"ValueError", "KeyError", "IndexError", "ZeroDivisionError",
             "UnicodeDecodeError", "JSONDecodeError"},
    "모듈·설치": {"ImportError", "ModuleNotFoundError"},
    "파일·권한": {"FileNotFoundError", "FileExistsError", "PermissionError",
             "IsADirectoryError", "NotADirectoryError", "OSError"},
    "실행·자원": {"RuntimeError", "AssertionError", "RecursionError",
             "MemoryError", "TimeoutError", "ConnectionError"},
    "Streamlit": {"StreamlitDuplicateElementKey", "StreamlitDuplicateElementId",
                  "StreamlitAPIException"},
}
# Python tracebacks typically end with 'ErrorType: message'. Use the final
# exception line first, rather than a previous exception in a chained traceback.
_ERROR_LINE = re.compile(
    r"^(?:(?:[A-Za-z_][A-Za-z_0-9]*\.)+)?"
    r"([A-Za-z_][A-Za-z_0-9]*(?:Error|Exception))(?=\s*:|\s*$)"
)


def error_category(error_type):
    """Human-readable category for an extracted error, without guessing causes."""
    for category, names in ERROR_GROUPS.items():
        if error_type in names:
            return category
    return "기타·추가 확인 필요"


def classify_error(message):
    """Find a traceback's final exception first; never execute user code."""
    lines = (message or "").splitlines()
    for raw_line in reversed(lines):
        line = raw_line.strip()
        match = _ERROR_LINE.match(line)
        if match:
            error_type = match.group(1)
            return error_type, ERROR_DESCRIPTIONS.get(
                error_type, "이 오류의 정확한 원인은 실행 환경과 코드에 따라 달라질 수 있습니다."
            )
        # Some Streamlit exception identifiers do not end in Error/Exception.
        for name in ("StreamlitDuplicateElementKey", "StreamlitDuplicateElementId"):
            if line == name or line.startswith(name + ":"):
                return name, ERROR_DESCRIPTIONS[name]

    # Fallback for shortened messages that only mention an error name.
    text = message or ""
    for error_type in sorted(ERROR_DESCRIPTIONS, key=len, reverse=True):
        if re.search(r"\b" + re.escape(error_type) + r"\b", text):
            return error_type, ERROR_DESCRIPTIONS[error_type]
    match = re.search(r"\b([A-Za-z_][A-Za-z_0-9]*(?:Error|Exception))\b", text)
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
