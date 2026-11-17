"""Code Doctor: Streamlit project for Python error research and learning."""
import hashlib
import html
import os

import pandas as pd
import streamlit as st

import checker
import security_guard
import database as db
import pypi_api
import stack_api
import translate_api
import upload_helper

st.set_page_config(page_title="Code Doctor", page_icon="🩺", layout="wide")
db.initialize()

LANGUAGES = {"한국어": "KO", "English (원문)": "EN", "日本語": "JA"}
ERROR_STATUS = ["미해결", "해결 중", "해결"]


def deepl_key():
    try:
        return st.secrets.get("DEEPL_API_KEY", "") or os.getenv("DEEPL_API_KEY", "")
    except (FileNotFoundError, OSError):
        return os.getenv("DEEPL_API_KEY", "")


def init_state():
    defaults = {"results": [], "answers": [], "last_record_id": None,
                "query": "", "question_id": None, "quota": None}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()

# Theme preference is per browser session; no database or API behavior changes.
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
with st.sidebar:
    st.toggle("🌙 다크 모드", key="dark_mode", help="밝은 화면과 어두운 화면을 전환합니다.")

dark = st.session_state.dark_mode
bg = "#0b1220" if dark else "#f4f7ff"
surface = "#141f32" if dark else "#ffffff"
foreground = "#e8efff" if dark else "#18243a"
muted = "#a6b5cf" if dark else "#53627a"
border = "#30405d" if dark else "#dce5f6"
sidebar_bg = "#101b2e" if dark else "#eaf0ff"
input_bg = "#17243a" if dark else "#ffffff"
st.markdown(
    f"""<style>
    .stApp {{background: {bg}; color: {foreground};}}
    [data-testid="stSidebar"] {{background: {sidebar_bg}; border-right: 1px solid {border};}}
    [data-testid="stHeader"] {{background: {bg};}}
    .stApp h1, .stApp h2, .stApp h3, .stApp p,
    .stApp label, .stApp [data-testid="stMarkdownContainer"] {{color: {foreground};}}
    .stApp [data-testid="stCaptionContainer"] {{color: {muted};}}
    .stApp [data-testid="stVerticalBlockBorderWrapper"] {{
        border-color: {border}; border-radius: 16px;
    }}
    .stApp [data-testid="stTextInput"] input,
    .stApp [data-testid="stTextArea"] textarea {{
        background: {input_bg}; color: {foreground}; border-radius: 10px;
        border: 1px solid {border};
    }}
    .stApp [data-testid="stSelectbox"] > div > div {{
        background: {input_bg}; color: {foreground}; border-radius: 10px;
    }}
    .stApp .stButton button[kind="primary"],
    .stApp .stFormSubmitButton button[kind="primary"] {{
        background: linear-gradient(110deg, #4169e1, #8055df);
        border: none; color: #fff; border-radius: 10px;
    }}
    .stApp .stButton button:hover, .stApp .stFormSubmitButton button:hover {{
        border-color: #7189ff;
    }}
    .doctor-hero {{
        background: linear-gradient(115deg, #305bc9 0%, #6949b7 65%, #178fa6 100%);
        padding: 1.5rem 1.8rem; border-radius: 20px;
        margin-bottom: 1.3rem; box-shadow: 0 8px 24px #172f6426;
    }}
    .doctor-hero h1 {{color: #fff !important; margin: 0; font-size: 2.25rem;}}
    .doctor-hero p {{color: #e9efff !important; margin: .35rem 0 0;}}
    .doctor-pill {{
        display: inline-block; padding: .25rem .7rem; border-radius: 999px;
        background: #ffffff24; color: white; font-size: .78rem; margin-bottom: .5rem;
    }}
    .doctor-note {{
        background: {surface}; border: 1px solid {border};
        border-left: 4px solid #6685ee; padding: .8rem 1rem;
        border-radius: 12px; color: {foreground}; margin-bottom: 1rem;
    }}
    /* Smartphone/tablet layout: stack inputs instead of squeezing two columns. */
    @media (max-width: 768px) {{
        .stApp [data-testid="stMainBlockContainer"] {{
            padding: 1.25rem 0.9rem 3rem !important;
        }}
        .doctor-hero {{
            padding: 1.15rem 1rem;
            border-radius: 14px;
            margin-bottom: 0.9rem;
            box-shadow: 0 5px 16px #172f6420;
        }}
        .doctor-hero h1 {{
            font-size: 1.7rem;
            line-height: 1.25;
        }}
        .doctor-hero p {{
            font-size: 0.88rem;
            line-height: 1.5;
        }}
        .doctor-pill {{ font-size: 0.7rem; }}
        .doctor-note {{ font-size: 0.88rem; padding: 0.7rem 0.8rem; }}
        .stApp [data-testid="stHorizontalBlock"] {{
            flex-wrap: wrap !important;
            row-gap: 0.75rem;
        }}
        .stApp [data-testid="column"] {{
            flex: 1 1 100% !important;
            min-width: 0 !important;
            width: 100% !important;
        }}
        .stApp [data-testid="stDataFrame"] {{
            max-width: 100%;
            overflow-x: auto;
        }}
        .stApp .stButton button,
        .stApp .stFormSubmitButton button {{ min-height: 2.65rem; }}
    }}
    </style>""",
    unsafe_allow_html=True,
)
st.markdown(
    """<div class="doctor-hero">
    <span class="doctor-pill">DEVELOPER TOOL · v1.1</span>
    <h1>🩺 Code Doctor</h1>
    <p>코드 오류를 진단하고, 해결 방법을 찾고, 경험을 기록하세요.</p>
    </div>""",
    unsafe_allow_html=True,
)
page = st.sidebar.radio("메뉴", ["오류 분석·검색", "저장 기록", "오류 통계", "API·사용 안내"])
st.sidebar.markdown("---")
st.sidebar.caption("Code Doctor · 개발자 오류 해결 도구")
display_lang = st.sidebar.selectbox("설명 언어", list(LANGUAGES), index=0)
target_language = LANGUAGES[display_lang]
st.sidebar.caption("사용자 코드는 실행하지 않으며, 코드 전체를 외부 API에 전송하지 않습니다.")


def answer_view(answer, question):
    body = answer.get("body", "")
    author = answer.get("owner", {}).get("display_name", "알 수 없음")
    answer_id = answer.get("answer_id")
    st.markdown(f"**답변 작성자:** {html.unescape(author)} · 추천 {answer.get('score', 0)}"
                + (" · ✅ 채택 답변" if answer.get("is_accepted") else ""))
    st.caption("내용은 Stack Overflow 이용자가 작성했습니다. 해결 여부는 직접 검증하세요.")
    if target_language == "EN":
        body_text = translate_api.translate_answer_html(body, "EN", "")
    else:
        try:
            with st.spinner("설명을 번역하는 중... (처음 요청 시 API 사용)"):
                body_text = translate_api.translate_answer_html(body, target_language, deepl_key())
        except translate_api.TranslationError as exc:
            st.warning(str(exc) + " 원문을 대신 표시합니다.")
            body_text = translate_api.translate_answer_html(body, "EN", "")
    st.markdown(body_text or "본문이 없습니다.")
    # Keep navigation on the trusted, expected host.
    link = answer.get("link", "")
    if link.startswith("https://stackoverflow.com/") or link.startswith("http://stackoverflow.com/"):
        st.link_button("Stack Overflow 원본 답변 열기", link)
    st.caption("출처: Stack Overflow · 작성자 및 원본 링크를 함께 표기 · 번역 시 DeepL 사용")
    if st.session_state.last_record_id:
        if st.button("이 답변을 현재 오류 기록에 북마크", key=f"bm_{answer_id}"):
            added = db.add_bookmark(st.session_state.last_record_id, question, answer)
            st.success("참고 자료를 기록에 연결했습니다." if added else "이미 저장된 참고 자료입니다.")
    else:
        st.info("참고 자료를 북마크하려면 먼저 위쪽에서 오류 기록을 저장하세요.")


if page == "오류 분석·검색":
    st.markdown('<div class="doctor-note">🔎 <b>진단 시작</b> · 오류 메시지나 코드를 입력하면 로컬에서 먼저 분석합니다.</div>', unsafe_allow_html=True)
    st.subheader("1. 오류 또는 코드 입력")
    st.caption("Python .py 파일을 끌어 놓으면 아래 코드 입력창에 내용이 채워집니다. 파일을 실행하지 않습니다.")
    upload = st.file_uploader("📁 Python 파일 끌어놓기 또는 선택", type=["py"], key="python_upload")
    if upload is None:
        st.session_state.pop("last_upload_token", None)
    elif upload.size > upload_helper.MAX_FILE_BYTES:
        st.error("업로드 파일은 512KB 이하여야 합니다.")
    else:
        raw_bytes = upload.getvalue()
        upload_token = (upload.name, hashlib.sha256(raw_bytes).hexdigest())
        if st.session_state.get("last_upload_token") != upload_token:
            try:
                imported_source = upload_helper.decode_python_upload(upload.name, raw_bytes)
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.session_state["code_input"] = imported_source
                st.session_state["last_upload_token"] = upload_token
                st.success(f"{upload.name} 파일을 읽었습니다. 아래 코드를 검토해 주세요.")

    col1, col2 = st.columns(2)
    with col1:
        title = st.text_input("오류 기록 제목", placeholder="예: Streamlit 버튼 key 중복")
        language = st.selectbox("프로그래밍 언어", ["python", "javascript", "java", "c#", "전체"])
        environment = st.selectbox("개발 환경", ["VS Code", "Streamlit", "Colab", "PyCharm", "기타"])
        error_message = st.text_area("오류 메시지 (선택)", height=145,
                                     placeholder="예: NameError: name 'x' is not defined")
    with col2:
        code = st.text_area("검사할 Python 코드 (선택 · 서버에서 실행하지 않음)", height=245,
                            placeholder="x = 10\nif x > 5:\n    print(x)", key="code_input")
    description = st.text_area("오류가 발생한 상황 (선택)")
    expected = st.text_input("예상 결과 (선택)")
    actual = st.text_input("실제 결과 (선택)")

    privacy_findings = security_guard.scan_fields({
        "오류 메시지": error_message,
        "코드": code,
        "발생 상황": description,
        "예상 결과": expected,
        "실제 결과": actual,
    })
    if privacy_findings:
        places = ", ".join(
            f"{item['field']} {item['line']}행 ({item['kind']})"
            for item in privacy_findings[:5]
        )
        st.warning(
            f"⚠️ 민감정보로 의심되는 내용 {len(privacy_findings)}개를 발견했어요: {places}. "
            "비밀번호, API 키, 이메일 등을 제거한 뒤 저장하거나 검색하세요. "
            "이 검사는 일부 패턴만 감지하며 모든 민감정보를 찾아내지는 못합니다."
        )

    error_type, explanation = checker.classify_error(error_message)
    st.subheader("2. 로컬 오류 분석")
    if error_type:
        st.info(f"**추출된 오류 유형:** {error_type}\n\n**분류:** {checker.error_category(error_type)}\n\n{explanation}")
    elif error_message:
        st.info("오류 유형을 자동 추출하지 못했습니다. 아래에 검색어를 직접 입력할 수 있어요.")
    if code.strip():
        if language == "python":
            syntax_result = checker.check_python(code)
            if syntax_result["passed"]:
                st.success(syntax_result["message"])
            else:
                st.error(f"{syntax_result['error_type']} · {syntax_result.get('line')}행, {syntax_result.get('column')}열: {syntax_result['message']}")
        else:
            st.warning("코드 문법 검사는 Python만 지원해요. 다른 언어는 오류 자료 검색만 가능합니다.")
    else:
        st.caption("코드를 입력하면 Python 문법을 검사할 수 있습니다. 문법 통과는 정상 실행을 보장하지 않아요.")

    with st.expander("오류 기록에 저장", expanded=False):
        cause = st.text_area("직접 확인한 원인", key="new_cause")
        solution = st.text_area("직접 확인한 해결 방법", key="new_solution")
        status = st.selectbox("상태", ERROR_STATUS)
        store_code = st.checkbox("내 코드도 로컬 DB에 저장 (비밀번호·토큰 확인 후 선택)", value=False)
        if st.button("SQLite에 오류 기록 저장", type="primary"):
            if not title.strip():
                st.error("오류 기록 제목을 입력하세요.")
            elif not (error_message.strip() or code.strip() or description.strip()):
                st.error("오류 메시지, 코드, 발생 상황 중 하나 이상을 입력하세요.")
            elif security_guard.scan_fields({
                "제목": title,
                "오류 메시지": error_message,
                "코드": code if store_code else "",
                "발생 상황": description,
                "예상 결과": expected,
                "실제 결과": actual,
                "원인": cause,
                "해결 방법": solution,
            }):
                st.error("민감정보가 의심되는 내용을 삭제하거나 가린 후 저장해 주세요.")
            else:
                record_id = db.create_error({"title": title.strip(), "language": language,
                    "environment": environment, "error_type": error_type,
                    "error_message": error_message, "source_code": code if store_code else "",
                    "description": description, "expected": expected, "actual": actual,
                    "cause": cause, "solution": solution, "status": status})
                st.session_state.last_record_id = record_id
                st.success(f"오류 기록 #{record_id}를 저장했어요. '저장 기록' 메뉴에서 볼 수 있습니다.")

    st.subheader("3. Stack Overflow 질문 검색")
    st.caption("외부에는 아래 검색어와 언어 태그만 전송됩니다. 입력한 코드나 전체 오류 메시지는 전송하지 않습니다.")
    auto_query = checker.suggest_query(error_message, language)
    if st.button("오류 메시지에서 검색어 추출"):
        st.session_state.query = auto_query
    st.text_input("API로 보낼 검색어 (직접 수정 가능)", key="query", placeholder="예: StreamlitDuplicateElementKey")
    if st.button("관련 질문 10개 검색", type="primary"):
        if not st.session_state.query.strip():
            st.error("검색어를 입력하거나 '오류 메시지에서 검색어 추출'을 눌러주세요.")
        elif security_guard.scan_text(st.session_state.query):
            st.error("검색어에 민감정보가 의심되는 내용이 있습니다. 제거한 뒤 다시 검색하세요.")
        else:
            try:
                with st.spinner("Stack Overflow 질문을 검색하는 중..."):
                    data = stack_api.search_questions(st.session_state.query, language)
                st.session_state.results = data.get("items", [])
                st.session_state.answers = []
                st.session_state.question_id = None
                st.session_state.quota = data.get("quota_remaining")
                st.success(f"{len(st.session_state.results)}개 질문을 가져왔어요.")
            except (stack_api.APIError, ValueError) as exc:
                st.error(str(exc))
    if st.session_state.quota is not None:
        st.caption(f"Stack Exchange API 남은 요청 한도: {st.session_state.quota}")
    questions = st.session_state.results
    if questions:
        labels = [f"{i+1}. {html.unescape(q.get('title','제목 없음'))[:95]}  ·  답변 {q.get('answer_count', 0)}개"
                  for i,q in enumerate(questions)]
        idx = st.selectbox("검색 결과에서 질문 선택", range(len(labels)), format_func=lambda i: labels[i])
        q = questions[idx]
        st.write(f"**추천 점수:** {q.get('score', 0)} · **태그:** {', '.join(q.get('tags', []))}")
        st.caption(f"질문 작성자: {html.unescape(q.get('owner',{}).get('display_name','알 수 없음'))}")
        if q.get("body"):
            with st.expander("질문 상세 내용 (영어 원문)"):
                st.markdown(translate_api.translate_answer_html(q["body"], "EN", ""))
        link = q.get("link", "")
        if link.startswith("https://stackoverflow.com/") or link.startswith("http://stackoverflow.com/"):
            st.link_button("질문 원본 보기", link)
        if st.button("이 질문의 실제 답변 가져오기"):
            try:
                with st.spinner("답변을 가져오는 중..."):
                    data = stack_api.fetch_answers(q["question_id"])
                st.session_state.answers = data.get("items", [])
                st.session_state.question_id = q["question_id"]
                st.success(f"{len(st.session_state.answers)}개 답변을 가져왔어요.")
            except (stack_api.APIError, ValueError) as exc:
                st.error(str(exc))
        if st.session_state.question_id == q.get("question_id") and st.session_state.answers:
            answers = st.session_state.answers
            a_idx = st.selectbox("답변 선택", range(len(answers)),
                format_func=lambda i: f"{'✓ 채택 · ' if answers[i].get('is_accepted') else ''}추천 {answers[i].get('score', 0)}점 · 답변 {i+1}")
            answer_view(answers[a_idx], q)
    st.subheader("4. Python 패키지 정보 (PyPI)")
    package_hint = checker.extract_missing_module(error_message)
    package_name = st.text_input("패키지명", value=package_hint,
                                 help="모듈 이름과 PyPI 패키지명이 다를 수 있습니다.")
    if st.button("PyPI 패키지 조회"):
        try:
            pkg = pypi_api.lookup_package(package_name)
            if not pkg:
                st.warning("PyPI에서 해당 패키지를 찾지 못했어요.")
            else:
                st.success(f"{pkg['name']} · 버전 {pkg['version']}")
                st.write(pkg["summary"] or "패키지 설명이 없습니다.")
                st.write("요구 Python 버전:", pkg["requires_python"])
                st.link_button("PyPI 공식 페이지", pkg["url"])
                st.caption("이 정보만으로 내 컴퓨터의 설치 여부를 확인할 수는 없습니다.")
        except (RuntimeError, ValueError) as exc:
            st.error(str(exc))

elif page == "저장 기록":
    st.markdown('<div class="doctor-note">📚 <b>나의 해결 기록</b> · 이전 오류를 검색하고 해결 과정을 관리하세요.</div>', unsafe_allow_html=True)
    st.subheader("SQLite에 저장된 오류 기록")
    col1, col2 = st.columns([2, 1])
    search = col1.text_input("기록 검색 (제목·오류 유형·메시지·해결 방법)")
    status_filter = col2.selectbox("상태 필터", ["전체", *ERROR_STATUS])
    rows = db.list_errors(search, status_filter)
    if not rows:
        st.info("해당하는 저장 기록이 없습니다.")
    else:
        st.dataframe(pd.DataFrame(rows)[["id", "title", "error_type", "status", "created_at"]],
                     hide_index=True, use_container_width=True)
        ids = [r["id"] for r in rows]
        record_id = st.selectbox("수정하거나 확인할 기록", ids,
                                 format_func=lambda x: f"#{x} · {next(r['title'] for r in rows if r['id']==x)}")
        record = db.get_error(record_id)
        with st.form(f"edit_{record_id}"):
            new_title = st.text_input("제목", value=record["title"])
            new_status = st.selectbox("해결 상태", ERROR_STATUS,
                                     index=ERROR_STATUS.index(record["status"]))
            new_cause = st.text_area("원인", value=record["cause"])
            new_solution = st.text_area("해결 방법", value=record["solution"])
            new_desc = st.text_area("발생 상황", value=record["description"])
            submitted = st.form_submit_button("수정 사항 저장", type="primary")
        if submitted:
            if not new_title.strip():
                st.error("제목은 비울 수 없어요.")
            else:
                db.update_error(record_id, {"title": new_title, "status": new_status,
                    "cause": new_cause, "solution": new_solution, "description": new_desc})
                st.success("변경 사항이 저장되었습니다.")
                st.rerun()
        with st.expander("저장된 오류 상세 보기"):
            st.write("**오류 메시지**")
            st.code(record["error_message"] or "(없음)", language=None)
            if record["source_code"]:
                st.write("**저장된 코드**")
                st.code(record["source_code"], language="python")
            st.write("**예상 결과:**", record["expected"] or "(없음)")
            st.write("**실제 결과:**", record["actual"] or "(없음)")
        with st.expander("연결된 참고 자료"):
            refs = db.list_bookmarks(record_id)
            if not refs:
                st.caption("아직 연결된 참고 자료가 없습니다.")
            for ref in refs:
                st.markdown(f"- [{html.unescape(ref['question_title'])}]({ref['question_url']})"
                            + (f" · 답변 ID {ref['answer_id']}" if ref["answer_id"] else ""))
        st.divider()
        confirm = st.checkbox("이 기록을 영구 삭제하는 데 동의합니다.", key=f"confirm_{record_id}")
        if st.button("기록 삭제", disabled=not confirm):
            db.delete_error(record_id)
            if st.session_state.last_record_id == record_id:
                st.session_state.last_record_id = None
            st.success("기록을 삭제했습니다.")
            st.rerun()

elif page == "오류 통계":
    st.markdown('<div class="doctor-note">📊 <b>오류 분석 대시보드</b> · 저장된 기록의 유형과 해결 상태를 확인하세요.</div>', unsafe_allow_html=True)
    st.subheader("저장된 오류의 유형과 해결 현황")
    statuses, categories = db.statistics()
    if not statuses:
        st.info("먼저 오류 기록을 등록하면 통계가 표시됩니다.")
    else:
        st.markdown("**해결 상태별 기록 수**")
        st.bar_chart(pd.DataFrame(statuses).set_index("status")["count"])
        st.markdown("**오류 유형별 기록 수**")
        st.bar_chart(pd.DataFrame(categories).set_index("error_type")["count"])
        st.caption("통계는 외부 데이터가 아니라 사용자가 SQLite에 저장한 기록을 바탕으로 계산합니다.")

elif page == "API·사용 안내":
    st.subheader("연결 상태 및 사용 안내")
    key = deepl_key()
    if key:
        st.success(
        "DeepL API 키 설정을 찾았습니다. 번역 요청으로 실제 작동 여부를 확인하세요."
        )
    else:
        st.warning(
        "DeepL API 키를 찾지 못했습니다. "
        ".streamlit/secrets.toml의 DEEPL_API_KEY 값을 확인하세요."
        )
    st.write("**Stack Exchange API:** 공개 질문 검색은 키 없이 사용 가능합니다.")
    st.write("**PyPI API:** 공개 패키지 조회는 키 없이 사용 가능합니다.")
    st.markdown("""
    **프로그램 사용 순서**
    1. 오류 메시지나 Python 코드를 입력해 오류 유형·문법을 확인합니다.
    2. 전송할 검색어를 직접 확인·수정한 뒤 Stack Overflow를 검색합니다.
    3. 질문과 답변을 골라 확인합니다. 한국어/일본어 선택 시 DeepL 번역을 시도합니다.
    4. 직접 확인한 원인과 해결 방법을 기록하고 저장합니다.
    5. 저장 기록에서 검색·수정·삭제하고 통계에서 결과를 확인합니다.

    **주의 사항**
    - 코드를 실행하지 않으므로 실행 오류나 논리 오류를 자동 검증하지 않습니다.
    - 오류 메시지에 비밀번호, API 키, 개인정보가 포함되어 있다면 입력 전에 제거하세요.
    - 질문/답변은 외부 커뮤니티 작성자의 내용이며 정답을 보장하지 않습니다.
    - Stack Overflow 답변은 해당 게시물의 라이선스·원문 출처를 확인하세요.
    - SQLite는 이 컴퓨터의 로컬 폴더에 저장됩니다. 프로젝트 폴더를 삭제하면 기록도 사라집니다.
    """)
    st.markdown("공식 문서: [Stack Exchange API](https://api.stackexchange.com/docs) · "
                "[DeepL](https://developers.deepl.com/docs) · "
                "[PyPI JSON API](https://docs.pypi.org/api/json/)")
