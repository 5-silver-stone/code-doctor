"""Non-executing explanation of common JavaScript, Java and C# error logs.

This is traceback/message recognition, NOT a compiler or a full syntax checker.
"""
import re

ERRORS = {
    "javascript": {
        "ReferenceError": ("정의되지 않은 변수 등을 참조했을 수 있습니다.", "변수·참조"),
        "TypeError": ("값의 자료형이나 속성 사용이 맞지 않을 수 있습니다.", "자료형"),
        "SyntaxError": ("JavaScript 구문을 확인하세요.", "문법"),
        "RangeError": ("허용 범위를 벗어난 값이 전달됐을 수 있습니다.", "값·범위"),
        "URIError": ("URI 인코딩이나 디코딩 입력을 확인하세요.", "값·형식"),
        "AggregateError": ("여러 개의 오류가 하나로 묶인 경우입니다.", "실행"),
        "ERR_MODULE_NOT_FOUND": ("import한 모듈의 경로와 설치 상태를 확인하세요.", "모듈"),
        "MODULE_NOT_FOUND": ("요청한 모듈을 찾지 못했습니다. 설치와 경로를 확인하세요.", "모듈"),
    },
    "java": {
        "NullPointerException": ("null인 객체에 접근했을 수 있습니다.", "변수·참조"),
        "ArrayIndexOutOfBoundsException": ("배열 인덱스가 범위를 벗어났을 수 있습니다.", "값·범위"),
        "ClassNotFoundException": ("클래스 경로나 의존성을 확인하세요.", "모듈"),
        "NoClassDefFoundError": ("실행 시 클래스 또는 의존성을 찾지 못했을 수 있습니다.", "모듈"),
        "IllegalArgumentException": ("메서드에 전달한 인자를 확인하세요.", "값·형식"),
        "NumberFormatException": ("숫자로 변환하려는 문자열의 형식을 확인하세요.", "값·형식"),
        "ArithmeticException": ("0으로 나누기 등 계산 오류를 확인하세요.", "계산"),
        "IOException": ("파일과 입출력 작업을 확인하세요.", "파일·입출력"),
        "ConcurrentModificationException": ("컬렉션 순회 중 변경 여부를 확인하세요.", "실행"),
    },
    "c#": {
        "NullReferenceException": ("null인 객체의 멤버에 접근했을 수 있습니다.", "변수·참조"),
        "IndexOutOfRangeException": ("배열 또는 컬렉션 인덱스를 확인하세요.", "값·범위"),
        "ArgumentException": ("메서드 인자의 값과 자료형을 확인하세요.", "값·형식"),
        "InvalidOperationException": ("현재 객체 상태에서 허용되지 않는 작업인지 확인하세요.", "실행"),
        "FileNotFoundException": ("대상 파일과 경로를 확인하세요.", "파일·입출력"),
        "FormatException": ("문자열을 변환하는 형식을 확인하세요.", "값·형식"),
        "DivideByZeroException": ("0으로 나누는 계산이 있는지 확인하세요.", "계산"),
    },
}

def classify_log(message, language):
    """Return (error_type, explanation, category) without executing any code."""
    definitions = ERRORS.get((language or "").lower())
    if not definitions or not isinstance(message, str):
        return "", "지원하는 오류 로그를 입력해 주세요.", "기타"
    # Prefer the last matching error name in chained logs.
    # Match full words and require likely diagnostic context to avoid code snippets.
    names = sorted(definitions, key=len, reverse=True)
    found = None
    for line in message.splitlines():
        text = line.strip()
        for name in names:
            if re.search(r"(?<![A-Za-z_0-9])" + re.escape(name) + r"(?![A-Za-z_0-9])", text):
                found = name
                break
        if (language or "").lower() == "c#":
            match = re.search(r"\berror\s+(CS\d{4,5})\b", text, re.I)
            if match:
                return match.group(1).upper(), "C# 컴파일 오류 코드입니다. 메시지와 해당 코드 줄을 확인하세요.", "컴파일·문법"
    if not found:
        return "", "알려진 오류 유형을 찾지 못했습니다. 전체 오류 메시지를 입력하거나 검색해 주세요.", "기타"
    explanation, group = definitions[found]
    return found, explanation, group
