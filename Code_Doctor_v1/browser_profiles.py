"""Lightweight device-local learning profiles, not server authentication.

Data stays in browser localStorage. A four-digit PIN is a convenience lock,
not strong protection; never store credentials, API keys or private code here.
"""
import copy
from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
import re

import security_guard

STORAGE_KEY = "codedoctor_local_profiles_v1"
MAX_NOTES = 100


def load_bundle(raw):
    if raw is None:
        return {"version": 1, "accounts": {}}
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (ValueError, TypeError):
            raise ValueError("브라우저 저장 데이터가 손상되었습니다.") from None
    if not isinstance(raw, dict) or not isinstance(raw.get("accounts"), dict):
        raise ValueError("브라우저 저장 데이터 형식이 올바르지 않습니다.")
    return copy.deepcopy(raw)


def _key(name):
    clean = (name or "").strip()
    if not re.fullmatch(r"[\w가-힣 -]{2,20}", clean, re.UNICODE):
        raise ValueError("이름은 2~20자의 글자·숫자·공백·밑줄·하이픈으로 입력하세요.")
    return clean.casefold()


def _pin(pin):
    if not isinstance(pin, str) or not re.fullmatch(r"\d{4}", pin):
        raise ValueError("비밀번호는 숫자 4자리여야 합니다.")
    return pin


def _digest(pin, salt_hex):
    return hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), bytes.fromhex(salt_hex), 150_000).hex()


def signup(bundle, name, pin):
    key = _key(name)
    _pin(pin)
    result = copy.deepcopy(bundle)
    accounts = result.setdefault("accounts", {})
    if key in accounts:
        raise ValueError("이 브라우저에 같은 이름의 프로필이 이미 있습니다.")
    if len(accounts) >= 20:
        raise ValueError("브라우저당 프로필은 최대 20개까지 만들 수 있습니다.")
    salt = os.urandom(16).hex()
    accounts[key] = {
        "display": name.strip(),
        "salt": salt,
        "pin_hash": _digest(pin, salt),
        "notes": [],
    }
    return result


def authenticate(bundle, name, pin):
    # Always require a known local account; there is no online account lookup.
    try:
        key = _key(name)
        _pin(pin)
        account = bundle.get("accounts", {}).get(key)
        return bool(account and hmac.compare_digest(_digest(pin, account["salt"]), account["pin_hash"]))
    except (ValueError, KeyError, TypeError):
        return False


def list_account_names(bundle):
    return [item["display"] for item in bundle.get("accounts", {}).values()
            if isinstance(item, dict) and isinstance(item.get("display"), str)]


def add_note(bundle, name, title, detail):
    key = _key(name)
    title = (title or "").strip()
    detail = (detail or "").strip()
    if not title or len(title) > 100 or len(detail) > 3000:
        raise ValueError("제목은 1~100자, 설명은 최대 3000자로 입력하세요.")
    if security_guard.scan_fields({"제목": title, "내용": detail}):
        raise ValueError("개인정보 또는 비밀키가 의심되는 내용을 제거해 주세요.")
    result = copy.deepcopy(bundle)
    account = result.get("accounts", {}).get(key)
    if account is None:
        raise ValueError("로그인된 프로필을 찾지 못했습니다.")
    notes = account.setdefault("notes", [])
    if len(notes) >= MAX_NOTES:
        raise ValueError("기기별 기록은 최대 100개입니다.")
    notes.insert(0, {
        "title": title,
        "detail": detail,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    return result
