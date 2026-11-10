# Code Doctor v1

Python + Streamlit + SQLite + Stack Exchange API + DeepL API + PyPI API를 사용한 개인 오류 검색/해결 기록 관리 프로그램입니다.

## 요구 환경

- Python 3.10 이상 권장 (Windows, VS Code, 로컬 PC)
- 인터넷 연결 (외부 API용)
- DeepL **API용 키** (일반 웹 번역 계정 비밀번호 아님)

## 시작하기 (Windows)

1. ZIP을 압축 해제하여 `Code_Doctor_v1` 폴더를 엽니다.
2. 폴더의 `.streamlit/secrets.toml.example`을 복사해서 같은 위치에 `secrets.toml`이라는 이름을 붙입니다. (`secrets.toml.example`은 남겨둬도 됩니다.)
3. `secrets.toml` 내용의 `여기에_발급받은_DeepL_API_키_입력`을 발급받은 **DeepL API 키**로 교체하고 저장합니다. 따옴표는 남겨 둡니다.
4. VS Code에서 **터미널 → 새 터미널**을 열고 아래 명령을 실행합니다.

```powershell
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

5. 브라우저에 표시된 `http://localhost:8501` 사이트를 확인합니다. 종료는 터미널에서 `Ctrl+C`.

> `py`가 없다면 `python`으로 바꾸어 실행하세요.
> `.streamlit` 폴더는 숨김 폴더이므로 파일 탐색기에서 보이지 않으면 VS Code에서 확인하세요.
> **절대로 API 키를 채팅이나 GitHub에 올리지 마세요.** `.gitignore`에 해당 파일을 제외했습니다.

## 사용 순서

1. **오류 분석·검색** 메뉴에서 오류 메시지, 코드, 실행 환경 등을 입력합니다. 코드 검사는 Python만 지원하며 코드는 **실행하지 않습니다**.
2. 오류가 있다면 **오류 메시지에서 검색어 추출**을 누르고, 외부에 전송될 검색어를 확인·수정합니다.
3. **관련 질문 10개 검색**을 누릅니다. Stack Exchange API에서 관련 질문을 가져옵니다.
4. 질문을 고르고 **이 질문의 실제 답변 가져오기**를 누릅니다. 자동 번역은 사이드바의 설명 언어에 따라 시도됩니다.
5. **오류 기록에 저장**을 펼쳐 본인이 확인한 원인과 해결 방법을 적고 저장합니다.
6. 답변을 북마크하려면 해당 기록을 먼저 저장해 둡니다. 저장 기록 메뉴에서 수정·검색·삭제할 수 있습니다.
7. PyPI 조회는 패키지가 공개 저장소에 등록되었는지만 알려 주며 **내 PC에 설치됐는지는 확인하지 못합니다**.

## API 구성

- **Stack Exchange v2.3:** `/search/advanced`, `/questions/{ids}/answers`. 공개 데이터는 API 키 없이 기본 조회 가능. 사용량 제한 있음.
- **DeepL v2:** 번역 `POST /v2/translate`, 무료키 `:fx`는 `api-free.deepl.com`, 다른 API 키는 `api.deepl.com`. 처음 번역은 과금/문자량에 반영될 수 있습니다. 반복 번역은 SQLite 캐시 활용.
- **PyPI:** `GET https://pypi.org/pypi/<package>/json`, 공개 패키지 정보.

## 개인정보 / 안전 / 검증 범위

- 사용자의 코드는 `ast.parse`로 **문법만 검사**하며 실행하지 않습니다. 문법 검사가 통과해도 런타임 오류/논리 오류는 발생할 수 있습니다.
- 오류 검색 API에는 화면에 보이는 **검색어**만 전송합니다. 비밀번호, 실명, 토큰, 로컬 경로는 검색어에서 빼 주세요.
- 코드 저장은 선택 사항입니다. 코드를 저장하기 전 API 키/토큰 등의 비밀값이 없는지 확인하세요.
- Stack Overflow 커뮤니티 답변은 검증되지 않은 조언일 수 있습니다. 출처·작성자·원문 링크를 표시합니다.
- 번역은 해당 답변의 일반 텍스트만 대상으로 하고 `<code>`/`<pre>` 속 코드는 번역 요청에서 제외합니다.
- DB(`code_doctor.db`)는 로컬 프로젝트 폴더에 자동으로 생성됩니다.

## 자동 테스트

```powershell
py -m unittest discover -s tests -v
```

실제 API 테스트는 본인의 API 키와 인터넷 연결이 필요한 **수동 테스트**로 별도 수행해야 합니다. `docs/테스트_체크리스트.md` 참고.

## 폴더 구조

- `app.py`: 웹 화면
- `checker.py`: 오류 메시지 종류와 Python 문법 검사
- `stack_api.py`: Stack Overflow 검색 및 답변
- `translate_api.py`: DeepL 번역 및 코드 구간 보존
- `pypi_api.py`: 패키지 정보
- `database.py`: SQLite 등록/조회/검색/수정/삭제
- `tests/test_core.py`: 네트워크 요청을 모의 처리한 자동 단위 테스트
- `docs/`: 프로젝트 기획과 테스트 기록

## 공식 문서

- https://api.stackexchange.com/docs
- https://developers.deepl.com/docs
- https://docs.pypi.org/api/json/
