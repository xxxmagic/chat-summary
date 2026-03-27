import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DIALOGUES_JSON = DATA_DIR / "dialogues.json"
SUMMARIES_JSON = DATA_DIR / "summaries.json"

GROK_API_KEY = os.getenv("GROK_API_KEY", "")
GROK_BASE_URL = os.getenv("GROK_BASE_URL", "https://api.x.ai/v1")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-4-1-fast-non-reasoning")
SUMMARY_CHUNK_SIZE = int(os.getenv("SUMMARY_CHUNK_SIZE", "50"))
SUMMARY_MAX_FIELDS_PER_CATEGORY = int(os.getenv("SUMMARY_MAX_FIELDS_PER_CATEGORY", "5"))
SUMMARY_MAX_LIST_ITEMS = int(os.getenv("SUMMARY_MAX_LIST_ITEMS", "4"))
SUMMARY_MAX_VALUE_LENGTH = int(os.getenv("SUMMARY_MAX_VALUE_LENGTH", "120"))

LOW_SIGNAL_TERMS = {
    "", "unknown", "n/a", "na", "none", "null", "?", "-", "no info", "not sure",
}

CATEGORY_KEY_WEIGHTS = {
    "identity": {
        "name": 6.0, "names": 6.0, "gender": 5.0, "genders": 5.0,
        "age": 5.0, "city": 4.5, "country": 4.5,
        "phone": 6.0, "email": 6.0, "kik": 5.5, "telegram": 5.5, "whatsapp": 5.5,
    },
    "relationship": {
        "status": 6.0, "partner": 5.5, "married": 5.0, "single": 5.0, "children": 4.0,
    },
    "work_money": {
        "work": 4.5, "job": 4.5, "occupation": 4.5, "income": 4.0, "financial": 4.0,
    },
    "lifestyle": {
        "location": 4.5, "availability": 4.0, "schedule": 3.5, "hobbies": 3.5,
    },
    "sexual": {
        "orientation": 5.0, "interests": 4.5, "boundaries": 5.0, "preferences": 4.5,
    },
    "personality": {
        "traits": 4.5, "temperament": 4.0,
    },
}

app = Flask(__name__)

# ─── In-memory dialogues data (loaded from JSON) ─────────────────────────────

_dialogues_data: Dict[str, Any] = {"dialogues": []}
_dialogues_by_id: Dict[int, Dict[str, Any]] = {}
_summaries_lock = threading.Lock()


def load_dialogues_data() -> None:
    global _dialogues_data, _dialogues_by_id
    if not DIALOGUES_JSON.exists():
        return
    try:
        raw = json.loads(DIALOGUES_JSON.read_text(encoding="utf-8"))
        _dialogues_data = raw
        _dialogues_by_id = {d["dialogue_id"]: d for d in raw.get("dialogues", [])}
    except Exception as exc:
        print(f"[warn] Could not load {DIALOGUES_JSON}: {exc}")


def dialogues_ready() -> bool:
    return len(_dialogues_by_id) > 0


# ─── Summaries (file-based) ───────────────────────────────────────────────────

def _load_summaries_raw() -> Dict[str, Any]:
    if not SUMMARIES_JSON.exists():
        return {}
    try:
        return json.loads(SUMMARIES_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_summaries_raw(data: Dict[str, Any]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    SUMMARIES_JSON.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def default_summary_obj() -> Dict[str, Any]:
    return {
        "users": {
            "user": {
                "identity": {}, "work_money": {}, "lifestyle": {},
                "relationship": {}, "sexual": {}, "personality": {},
            },
            "persona": {
                "identity": {}, "work_money": {}, "lifestyle": {},
                "relationship": {}, "sexual": {}, "personality": {},
            },
        }
    }


def get_summary_state(dialogue_id: int) -> Dict[str, Any]:
    dialogue = _dialogues_by_id.get(dialogue_id)
    total_messages = dialogue["dialogue_length_messages"] if dialogue else 0

    with _summaries_lock:
        all_summaries = _load_summaries_raw()
        entry = all_summaries.get(str(dialogue_id))

    if not entry:
        summary = default_summary_obj()
        return {
            "dialogue_id": dialogue_id,
            "processed_messages": 0,
            "total_messages": total_messages,
            "is_complete": False,
            "summary": summary,
            "fact_count": count_summary_facts(summary),
            "updated_at": None,
        }

    try:
        summary_obj = entry["summary"] if isinstance(entry.get("summary"), dict) else json.loads(entry.get("summary_json", "{}"))
    except Exception:
        summary_obj = default_summary_obj()

    processed = entry.get("processed_messages", 0)
    return {
        "dialogue_id": dialogue_id,
        "processed_messages": processed,
        "total_messages": total_messages,
        "is_complete": processed >= total_messages,
        "summary": summary_obj,
        "fact_count": count_summary_facts(summary_obj),
        "updated_at": entry.get("updated_at"),
    }


def save_summary_state(dialogue_id: int, processed_messages: int, summary_obj: Dict[str, Any]) -> None:
    with _summaries_lock:
        all_summaries = _load_summaries_raw()
        all_summaries[str(dialogue_id)] = {
            "processed_messages": processed_messages,
            "summary": summary_obj,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        _save_summaries_raw(all_summaries)


# ─── Data access ─────────────────────────────────────────────────────────────

def fetch_target_dialogues() -> List[Dict[str, Any]]:
    return [
        {
            "dialogue_id": d["dialogue_id"],
            "dialogue_length_messages": d["dialogue_length_messages"],
            "dialogue_length_chars": d.get("dialogue_length_chars", 0),
        }
        for d in _dialogues_data.get("dialogues", [])
    ]


def fetch_messages(dialogue_id: int, lang: str = "sv") -> List[Dict[str, Any]]:
    dialogue = _dialogues_by_id.get(dialogue_id)
    if not dialogue:
        return []
    messages_by_lang = dialogue.get("messages", {})
    # Fall back to any available language
    msgs = messages_by_lang.get(lang) or messages_by_lang.get("sv") or []
    return list(msgs)


# ─── Summary limits / sanitization ───────────────────────────────────────────

def sanitize_scalar(value: Any) -> Any:
    if isinstance(value, str):
        text = value.strip()
        if len(text) > SUMMARY_MAX_VALUE_LENGTH:
            return text[: SUMMARY_MAX_VALUE_LENGTH - 1] + "…"
        return text
    if isinstance(value, (bool, int, float)):
        return value
    if value is None:
        return None
    text = str(value).strip()
    if len(text) > SUMMARY_MAX_VALUE_LENGTH:
        return text[: SUMMARY_MAX_VALUE_LENGTH - 1] + "…"
    return text


def scalar_importance(value: Any) -> float:
    if value is None:
        return -10.0
    if isinstance(value, bool):
        return 0.8
    if isinstance(value, (int, float)):
        return 1.0
    text = str(value).strip()
    if not text:
        return -10.0
    lowered = text.lower()
    if lowered in LOW_SIGNAL_TERMS:
        return -8.0
    score = 1.0
    if any(ch.isdigit() for ch in text):
        score += 0.6
    if "@" in text:
        score += 0.8
    if 4 <= len(text) <= 80:
        score += 0.4
    if len(text) > 120:
        score -= 0.4
    return score


def value_importance(value: Any) -> float:
    if isinstance(value, dict):
        if not value:
            return -10.0
        child_scores = [s for s in (value_importance(v) for v in value.values()) if s > -9.0]
        return -10.0 if not child_scores else 0.8 + sum(sorted(child_scores, reverse=True)[:3])
    if isinstance(value, list):
        if not value:
            return -10.0
        child_scores = [s for s in (value_importance(v) for v in value) if s > -9.0]
        return -10.0 if not child_scores else 0.6 + sum(sorted(child_scores, reverse=True)[:3])
    return scalar_importance(value)


def key_importance(category: Optional[str], key: str) -> float:
    normalized = key.strip().lower()
    base = 0.5
    if category:
        base += CATEGORY_KEY_WEIGHTS.get(category, {}).get(normalized, 0.0)
    if any(token in normalized for token in ("name", "phone", "email", "kik", "city", "status")):
        base += 1.0
    if len(normalized) <= 2:
        base -= 0.4
    return base


def sanitize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return sanitize_mapping(value, SUMMARY_MAX_FIELDS_PER_CATEGORY)
    if isinstance(value, list):
        out_list = []
        seen: set = set()
        for item in value[:SUMMARY_MAX_LIST_ITEMS]:
            normalized = sanitize_value(item)
            if normalized in ("", None, [], {}):
                continue
            marker = json.dumps(normalized, ensure_ascii=False, sort_keys=True, default=str)
            if marker in seen:
                continue
            seen.add(marker)
            out_list.append(normalized)
        return out_list
    return sanitize_scalar(value)


def sanitize_mapping(mapping: Dict[str, Any], max_fields: int, category: Optional[str] = None) -> Dict[str, Any]:
    scored: List[Tuple[float, str, Any]] = []
    for raw_key, raw_value in mapping.items():
        key = str(raw_key).strip()
        if not key:
            continue
        normalized = sanitize_value(raw_value)
        if normalized in ("", None, [], {}):
            continue
        score = key_importance(category, key) + value_importance(normalized)
        scored.append((score, key, normalized))
    scored.sort(key=lambda item: (-item[0], item[1].lower()))
    out: Dict[str, Any] = {}
    for score, key, normalized in scored:
        if len(out) >= max_fields:
            break
        if score <= -5.0:
            continue
        out[key] = normalized
    return out


def apply_summary_limits(summary_obj: Dict[str, Any]) -> Dict[str, Any]:
    result = default_summary_obj()
    users_in = summary_obj.get("users", {}) if isinstance(summary_obj, dict) else {}
    for person in ("user", "persona"):
        person_in = users_in.get(person, {}) if isinstance(users_in, dict) else {}
        if not isinstance(person_in, dict):
            person_in = {}
        for category in ("identity", "work_money", "lifestyle", "relationship", "sexual", "personality"):
            cat_in = person_in.get(category, {})
            result["users"][person][category] = (
                sanitize_mapping(cat_in, SUMMARY_MAX_FIELDS_PER_CATEGORY, category)
                if isinstance(cat_in, dict) else {}
            )
    return result


def count_summary_facts(node: Any) -> int:
    if isinstance(node, dict):
        return sum(count_summary_facts(v) for v in node.values())
    if isinstance(node, list):
        return sum(count_summary_facts(v) for v in node)
    if node is None:
        return 0
    if isinstance(node, str):
        return 1 if node.strip() else 0
    return 1


# ─── Prompt defaults ──────────────────────────────────────────────────────────

LANG_INSTRUCTIONS = {
    "ru": "Write all field VALUES in Russian.",
    "en": "Write all field VALUES in English.",
    "sv": "Write all field VALUES in Swedish.",
}


def default_system_prompt() -> str:
    schema_example = json.dumps(default_summary_obj(), ensure_ascii=False, indent=2)
    return (
        "You are an intelligence analyst building a factual profile of a person from a chat conversation.\n"
        "Your goal is NOT to summarize the conversation — your goal is to EXTRACT specific facts.\n"
        "\n"
        "Return ONLY valid JSON with this exact schema:\n"
        f"{schema_example}\n"
        "\n"
        "ROLES — strictly one person each:\n"
        "- users.user = the CLIENT: the real person who initiated contact\n"
        "- users.persona = the OPERATOR character: the person being played by the operator\n"
        "Determine roles from context. Keep them strictly separate — never mix.\n"
        "\n"
        "WHAT TO LOOK FOR in each category:\n"
        "- identity: name, age, city, country, contact handles (phone, kik, telegram, email)\n"
        "- work_money: job title, employer, income level, financial situation, debts\n"
        "- lifestyle: living situation (alone/family), daily schedule, hobbies, interests\n"
        "- relationship: marital status, partner, ex-partners, children, family situation\n"
        "- sexual: expressed desires, preferences, boundaries, orientation\n"
        "- personality: emotional state, communication style, red flags, manipulation tactics\n"
        "\n"
        "Language: {lang}\n"
        "\n"
        "Rules:\n"
        "- Only record facts explicitly stated or strongly implied — no guessing.\n"
        "- Preserve existing facts unless directly contradicted.\n"
        "- Each category = max 1-2 concise facts. No long prose.\n"
        "- identity.gender must be a single word: female or male (used internally, not shown).\n"
        "- Skip a category entirely if nothing is known — use empty object.\n"
        "- Respond with pure JSON only."
    )


def default_user_prompt() -> str:
    return (
        "Extract and update profile facts from the new messages below.\n"
        "Focus on finding real facts about the client: family, work, location, finances, relationships.\n\n"
        "previous_summary:\n"
        "{previous_summary}\n\n"
        "new_messages:\n"
        "{new_messages}"
    )


# ─── Grok call ────────────────────────────────────────────────────────────────

def call_grok_incremental_summary(
    previous_summary: Dict[str, Any],
    new_messages: List[Dict[str, Any]],
    system_prompt: Optional[str] = None,
    user_prompt: Optional[str] = None,
    lang: str = "en",
) -> Dict[str, Any]:
    if not GROK_API_KEY:
        raise RuntimeError("GROK_API_KEY is missing. Set it in .env file.")

    system_prompt = (system_prompt or "").strip() or default_system_prompt()
    user_prompt = (user_prompt or "").strip() or default_user_prompt()

    # Resolve {lang} placeholder in both prompts
    lang_instruction = LANG_INSTRUCTIONS.get(lang, f"Write all field VALUES in {lang}.")
    system_prompt = system_prompt.replace("{lang}", lang_instruction)
    user_prompt = user_prompt.replace("{lang}", lang_instruction)

    limits_note = (
        "\nHard limits — strictly enforce:\n"
        f"- max {SUMMARY_MAX_FIELDS_PER_CATEGORY} fields per category (keep only the most important ones)\n"
        f"- max {SUMMARY_MAX_LIST_ITEMS} items in any array field\n"
        f"- max {SUMMARY_MAX_VALUE_LENGTH} chars per value — be concise\n"
        "- Each category should read like a 1-line note, not a list of everything\n"
        "- Drop low-signal, repetitive, or uncertain facts\n"
        "- Prioritize: name, age, city, status, job, key interests — skip minor details"
    )
    if "Hard limits per category" not in system_prompt:
        system_prompt = system_prompt + limits_note

    rendered_user_prompt = (
        user_prompt
        .replace("{previous_summary}", json.dumps(previous_summary, ensure_ascii=False, indent=2))
        .replace("{new_messages}", json.dumps(new_messages, ensure_ascii=False, indent=2))
    )

    payload = {
        "model": GROK_MODEL,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": rendered_user_prompt},
        ],
    }
    response = requests.post(
        f"{GROK_BASE_URL.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {GROK_API_KEY}", "Content-Type": "application/json"},
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    if isinstance(content, list):
        content = "".join(
            chunk.get("text", "") if isinstance(chunk, dict) else str(chunk) for chunk in content
        )
    content = content.strip()

    if not content.startswith("{"):
        start = content.find("{")
        end = content.rfind("}")
        if start >= 0 and end > start:
            content = content[start : end + 1]

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        import re
        repaired = re.sub(r",\s*([}\]])", r"\1", content)
        try:
            parsed = json.loads(repaired)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Model returned invalid JSON even after repair: {exc}\nRaw: {content[:400]}"
            ) from exc

    return apply_summary_limits(parsed)


# ─── App startup ─────────────────────────────────────────────────────────────

load_dialogues_data()

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
def index() -> str:
    return render_template("index.html")


@app.get("/favicon.ico")
def favicon() -> Response:
    return Response(status=204)


@app.get("/api/status")
def api_status():
    return jsonify({
        "dialogues_ready": dialogues_ready(),
        "dialogue_count": len(_dialogues_by_id),
        "chunk_size": SUMMARY_CHUNK_SIZE,
    })


@app.get("/api/dialogues")
def api_dialogues():
    if not dialogues_ready():
        return jsonify([])
    return jsonify(fetch_target_dialogues())


@app.get("/api/summaries")
def api_summaries():
    if not dialogues_ready():
        return jsonify([])
    return jsonify([get_summary_state(d["dialogue_id"]) for d in fetch_target_dialogues()])


@app.get("/api/dialogues/<int:dialogue_id>/messages")
def api_messages(dialogue_id: int):
    lang = request.args.get("lang", "sv").strip()
    limit_raw = request.args.get("limit", "").strip()

    messages = fetch_messages(dialogue_id, lang)
    total = len(messages)

    if limit_raw:
        try:
            limit = max(1, int(limit_raw))
            messages = messages[:limit]
        except ValueError:
            pass

    return jsonify({
        "dialogue_id": dialogue_id,
        "total_messages": total,
        "returned_messages": len(messages),
        "lang": lang,
        "messages": messages,
    })


@app.get("/api/dialogues/<int:dialogue_id>/summary")
def api_summary(dialogue_id: int):
    return jsonify(get_summary_state(dialogue_id))


@app.post("/api/dialogues/<int:dialogue_id>/summary/reset")
def api_summary_reset(dialogue_id: int):
    save_summary_state(dialogue_id, 0, default_summary_obj())
    return jsonify(get_summary_state(dialogue_id))


@app.post("/api/dialogues/<int:dialogue_id>/summary/next")
def api_summary_next(dialogue_id: int):
    state = get_summary_state(dialogue_id)
    if state["is_complete"]:
        return jsonify({**state, "processed_in_this_step": 0, "status": "already_complete"})

    # Always summarise from the original Swedish messages for best quality
    all_messages = fetch_messages(dialogue_id, "sv")
    offset = state["processed_messages"]
    chunk = all_messages[offset : offset + SUMMARY_CHUNK_SIZE]

    if not chunk:
        return jsonify({**state, "processed_in_this_step": 0, "status": "no_new_messages"})

    body = request.get_json(silent=True) or {}
    system_prompt = body.get("system_prompt")
    user_prompt = body.get("user_prompt")
    lang = body.get("lang", "en")

    try:
        updated_summary = call_grok_incremental_summary(
            state["summary"],
            chunk,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            lang=lang,
        )
    except RuntimeError as exc:
        return jsonify({"error": str(exc), "status": "summary_failed"}), 400
    except Exception as exc:
        return jsonify({"error": str(exc), "status": "summary_failed"}), 500

    processed_messages = offset + len(chunk)
    save_summary_state(dialogue_id, processed_messages, updated_summary)
    new_state = get_summary_state(dialogue_id)
    return jsonify({**new_state, "processed_in_this_step": len(chunk), "status": "updated"})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=False)
