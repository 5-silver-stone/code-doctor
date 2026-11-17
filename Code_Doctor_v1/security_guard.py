"""Local-only warning scanner for common secrets in pasted code or error messages.

The scanner never executes supplied code, makes network requests, or returns
matched secret values. A warning is not proof that all secrets were detected.
"""
import re

# Rules intentionally favor common credential formats and assignments.
# Do not put the matched values into logs, database records, or UI messages.
_RULES = (
    ("개인 키", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("액세스 토큰", re.compile(
        r"\b(?:AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9_]{20,}|"
        r"github_pat_[A-Za-z0-9_]{20,}|sk-(?:proj-)?[A-Za-z0-9_-]{20,}|"
        r"xox[baprs]-[A-Za-z0-9-]{16,})\b"
    )),
    ("비밀번호/API 키", re.compile(
        r"(?i)\b(?:api[_-]?key|secret(?:[_-]?key)?|password|passwd|"
        r"access[_-]?token|auth[_-]?token|client[_-]?secret|"
        r"private[_-]?key)\b\s*(?::|=)\s*['\"][^'\"\r\n]{4,}['\"]"
    )),
    ("이메일 주소", re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    )),
)


def scan_text(text, *, max_findings=20):
    """Return [{'kind': str, 'line': int}], never values or text snippets."""
    if not isinstance(text, str) or not text:
        return []
    result = []
    # Bound work on unexpectedly large pastes.
    for line_number, line in enumerate(text[:200_000].splitlines(), 1):
        for kind, pattern in _RULES:
            if pattern.search(line):
                result.append({"kind": kind, "line": line_number})
                if len(result) >= max_findings:
                    return result
    return result


def scan_fields(fields, *, max_findings=20):
    """Scan a mapping of human-readable field labels to strings, locally."""
    result = []
    for field, value in fields.items():
        for item in scan_text(value, max_findings=max_findings - len(result)):
            result.append({"field": field, **item})
            if len(result) >= max_findings:
                return result
    return result
