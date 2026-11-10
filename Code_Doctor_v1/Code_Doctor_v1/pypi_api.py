"""Public PyPI JSON API lookup. This cannot inspect packages on a user's PC."""
import re
import requests


def lookup_package(name):
    name = (name or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", name):
        raise ValueError("패키지 이름에는 영문, 숫자, 점, 하이픈, 밑줄만 입력하세요.")
    try:
        res = requests.get(f"https://pypi.org/pypi/{name}/json", timeout=10)
        if res.status_code == 404:
            return None
        res.raise_for_status()
        info = res.json().get("info", {})
        return {"name": info.get("name", name), "version": info.get("version", "?"),
                "summary": info.get("summary", ""),
                "requires_python": info.get("requires_python", "정보 없음"),
                "url": f"https://pypi.org/project/{name}/"}
    except (requests.RequestException, ValueError) as exc:
        raise RuntimeError(f"PyPI 조회 실패: {exc}") from exc
