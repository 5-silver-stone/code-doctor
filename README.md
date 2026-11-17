# 🩺 Code Doctor v2.1

오류 메시지 분석, Python 문법 검사, Stack Overflow 검색, DeepL 번역, PyPI 패키지 조회, 개인 학습용 기록, 선택적 AI 디버깅을 제공하는 Streamlit 웹앱입니다.

**배포 사이트:** https://codedoctor.streamlit.app/

## 현재 주요 기능

- Python AST 기반 문법 검사, 오류 줄 강조 (코드를 실행하지 않음)
- Python·JavaScript·Java·C#의 대표적 오류 로그 유형 분류 (타 언어 구문 컴파일은 지원하지 않음)
- Python .py 파일 최대 10개 업로드 및 파일 선택 (최대 512KB/파일, 2MB 전체)
- Stack Overflow 검색과 세션별 최근 검색 기록
- DeepL 번역 및 PyPI 패키지 정보 조회 (설정/API 상황에 따라 이용 제한)
- SQLite 저장 기록 및 7·30·90일 등록 추세
- 다크 모드, 모바일 화면 구성
- **선택적 OpenAI AI 분석**: 원인 설명, 수정 예시, 초보자/전문가 모드, 후속 대화
- **베타:** 이 브라우저에만 남는 이름+4자리 PIN 프로필과 프로필별 로컬 메모

## Streamlit Community Cloud 배포 파일

현재 운영 앱의 진입점은 `Code_Doctor_v1/Code_Doctor_v1/app.py`이며, 이 파일이 실제 최신 코드인 `Code_Doctor_v1/app.py`를 호출합니다. 수정할 때는 **최신 코드 파일**을 편집하세요.

같은 이름의 중첩 폴더 내 이전 파일을 별도로 수정하거나 임의로 삭제하지 마세요.

## 선택적 AI 기능 설정

1. Streamlit Community Cloud → Code Doctor 앱 설정 → **Secrets**로 이동합니다.
2. 아래 형식으로 **서버 Secrets**에 등록합니다. 실제 API 키를 GitHub·코드·채팅에 넣지 마세요.
3. 앱의 `오류 분석·검색 → 🧠 AI 오류 원인 설명`을 펼친 뒤 전송할 내용을 검토하고 동의하면 사용할 수 있습니다.

```toml
OPENAI_API_KEY = "본인의_실제_API_KEY"
OPENAI_MODEL = "gpt-6-luna"
```

AI 사용은 별도 API 요금/한도 및 계정 사용 조건에 따릅니다. API 키가 없으면 AI 버튼은 비활성화됩니다. 코드는 사용자가 별도로 선택했을 때만 전송하고, 민감정보가 의심되는 경우 요청을 차단합니다. 정규식 검사는 모든 비밀정보를 보장하지 않습니다.

## 기기별 프로필의 중요 제한

- 온라인 인증 계정이 아닙니다. 브라우저 localStorage에 이름·PIN 해시·간단한 메모를 저장하는 **학습용 간편 기능**입니다.
- 4자리 PIN은 강한 보안이 아닙니다. 다른 기기/브라우저 동기화나 분실 복구를 제공하지 않습니다.
- 브라우저의 사이트 데이터를 삭제하면 로컬 프로필/메모를 잃을 수 있습니다.
- **기존 서버 SQLite 기록은 기기별 프로필과 분리되어 있지 않습니다.** 공용 서버 데이터베이스에 비밀 코드나 개인정보를 저장하지 마세요.
- CI에서 프로필 Python 로직과 모킹된 화면은 검사했으나, 실제 브라우저에서 localStorage 저장·복원은 별도 실사용 검증이 필요합니다.

## 테스트

```bash
python -m pip install -r Code_Doctor_v1/requirements.txt
python -m unittest discover -s Code_Doctor_v1/tests -p "test_*.py" -v
```

GitHub Actions는 PR 및 main 업데이트마다 회귀 테스트를 실행합니다. 외부 API 연결은 모킹하여 실제 인증/요청 성공 여부를 보장하지 않습니다.
