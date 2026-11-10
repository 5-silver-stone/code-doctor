"""DeepL text translation with source-code preserving HTML-to-Markdown conversion."""
import re
import requests
from bs4 import BeautifulSoup
from database import get_translation, save_translation

class TranslationError(Exception):
    pass

TOKEN_RE = re.compile(r"(CDCODE__\d+__)")


def html_to_markdown(html):
    """Turn untrusted Stack Overflow HTML into safe plain Markdown; do not render raw HTML."""
    soup = BeautifulSoup(html or "", "html.parser")
    for tag in soup(["script", "style", "iframe", "img", "form"]):
        tag.decompose()
    code_tokens = {}
    for tag in list(soup.find_all("pre")):
        token = f"CDCODE__{len(code_tokens)}__"
        raw = tag.get_text("", strip=False).strip("\n")
        code_tokens[token] = ("block", raw)
        tag.replace_with("\n" + token + "\n")
    for tag in list(soup.find_all("code")):
        token = f"CDCODE__{len(code_tokens)}__"
        code_tokens[token] = ("inline", tag.get_text("", strip=False))
        tag.replace_with(token)
    text = soup.get_text(separator="\n", strip=True)
    return text, code_tokens


def _reinsert_codes(text, tokens):
    for marker, (kind, code) in tokens.items():
        if kind == "block":
            fence = "````" if "```" in code else "```"
            text = text.replace(marker, f"\n\n{fence}\n{code}\n{fence}\n\n")
        else:
            text = text.replace(marker, "`" + code.replace("`", "'") + "`")
    return text


def get_deepl_endpoint(api_key):
    return ("https://api-free.deepl.com/v2/translate"
            if api_key.strip().endswith(":fx") else "https://api.deepl.com/v2/translate")


def translate_answer_html(html, target_language, api_key):
    """Translate ONLY prose; preserve code placeholders before DeepL receives any text."""
    plain, tokens = html_to_markdown(html)
    if target_language == "EN":
        return _reinsert_codes(plain, tokens)
    if not api_key or api_key.startswith("여기에"):
        raise TranslationError("DeepL API 키가 없습니다. .streamlit/secrets.toml을 설정하세요.")
    cached = get_translation(plain + repr(tokens), target_language)
    if cached is not None:
        return cached

    parts = TOKEN_RE.split(plain)
    indexes = []
    texts = []
    for i, p in enumerate(parts):
        if not p.strip() or p in tokens:
            continue
        # Limit per-item cost and prevent accidental huge translation requests.
        if len(p) > 4500:
            parts[i] = p[:4500] + "\n[긴 설명 일부는 원문으로 표시됨]\n" + p[4500:]
            continue
        indexes.append(i)
        texts.append(p)
    if not texts:
        result = _reinsert_codes(plain, tokens)
        save_translation(plain + repr(tokens), target_language, result)
        return result
    if sum(map(len, texts)) > 10000:
        raise TranslationError("답변이 너무 길어 번역 요청을 중단했습니다. 원문 링크를 확인하세요.")
    try:
        response = requests.post(
            get_deepl_endpoint(api_key),
            json={"text": texts, "target_lang": target_language},
            headers={"Authorization": f"DeepL-Auth-Key {api_key}", "Content-Type": "application/json"},
            timeout=22,
        )
        if response.status_code in (401, 403):
            raise TranslationError("DeepL 인증에 실패했습니다. 키가 API용인지 확인하세요.")
        if response.status_code == 456:
            raise TranslationError("DeepL 번역 사용 한도를 초과했습니다.")
        response.raise_for_status()
        translated = response.json()["translations"]
        if len(translated) != len(texts):
            raise TranslationError("DeepL이 예상한 개수의 번역 결과를 반환하지 않았습니다.")
        for idx, translated_text in zip(indexes, translated):
            parts[idx] = translated_text["text"]
    except requests.RequestException as exc:
        raise TranslationError(f"번역 요청에 실패했습니다: {exc}") from exc
    except (KeyError, ValueError, TypeError) as exc:
        raise TranslationError("번역 응답을 처리하지 못했습니다.") from exc
    output = _reinsert_codes("".join(parts), tokens)
    save_translation(plain + repr(tokens), target_language, output)
    return output
