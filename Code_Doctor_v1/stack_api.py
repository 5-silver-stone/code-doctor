"""Read-only Stack Overflow access through the public Stack Exchange API."""
import requests

BASE = "https://api.stackexchange.com/2.3"

class APIError(Exception):
    pass


def _get(path, params):
    try:
        response = requests.get(BASE + path, params=params, timeout=12,
                                headers={"User-Agent": "CodeDoctorSchoolProject/1.0"})
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise APIError(f"Stack Exchange 요청 실패: {exc}") from exc
    if "error_message" in data:
        raise APIError("Stack Exchange 오류: " + str(data["error_message"]))
    if data.get("backoff"):
        raise APIError(f"API가 {data['backoff']}초 동안 추가 요청 중단을 요구합니다. 해당 시간이 지난 뒤 다시 검색하세요.")
    return data


def search_questions(keyword, tag="python", limit=10):
    keyword = (keyword or "").strip()
    if not keyword:
        raise ValueError("검색어를 입력하세요.")
    params = {"site": "stackoverflow", "q": keyword[:180], "sort": "relevance",
              "pagesize": max(1, min(int(limit), 20)), "filter": "withbody"}
    if tag and tag.lower() != "전체":
        params["tagged"] = tag.lower()
    return _get("/search/advanced", params)


def fetch_answers(question_id):
    if not int(question_id) > 0:
        raise ValueError("질문 ID가 잘못되었습니다.")
    return _get(f"/questions/{int(question_id)}/answers",
                {"site": "stackoverflow", "sort": "votes", "order": "desc",
                 "pagesize": 10, "filter": "withbody"})
