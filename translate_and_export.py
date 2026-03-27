"""
One-time script: export 5 target dialogues from DuckDB and translate sv→ru + sv→en via Grok.
Output: data/dialogues.json
"""

import json
import os
import sys
import time
from pathlib import Path

import duckdb
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "dialogs.duckdb"
OUTPUT_PATH = BASE_DIR / "data" / "dialogues.json"

GROK_API_KEY = os.getenv("GROK_API_KEY", "")
GROK_BASE_URL = os.getenv("GROK_BASE_URL", "https://api.x.ai/v1")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-4-1-fast-non-reasoning")

BATCH_SIZE = 15  # messages per Grok call
RETRY_LIMIT = 3


def fetch_target_dialogues(limit: int = 5) -> list[dict]:
    con = duckdb.connect(str(DB_PATH))
    rows = con.execute(
        """
        WITH candidates AS (
            SELECT ds.dialogue_id, ds.dialogue_length_messages, ds.dialogue_length_chars
            FROM dialogue_stats ds
            JOIN (SELECT DISTINCT dialogue_id FROM dialogue WHERE lang = 'sv') sv USING (dialogue_id)
            WHERE ds.dialogue_length_messages BETWEEN 100 AND 500
        )
        , hashed AS (
            SELECT
                c.dialogue_id, c.dialogue_length_messages, c.dialogue_length_chars,
                md5(string_agg(d.sender_gender || ':' || d.message, '||' ORDER BY d.msg_order)) AS dialogue_hash
            FROM candidates c
            JOIN dialogue d USING (dialogue_id)
            GROUP BY 1, 2, 3
        )
        , dedup AS (
            SELECT dialogue_id, dialogue_length_messages, dialogue_length_chars,
                row_number() OVER (PARTITION BY dialogue_hash ORDER BY dialogue_id) AS hash_rank
            FROM hashed
        )
        SELECT dialogue_id, dialogue_length_messages, dialogue_length_chars
        FROM dedup WHERE hash_rank = 1
        ORDER BY dialogue_length_messages DESC, dialogue_id
        LIMIT ?;
        """,
        [limit],
    ).fetchall()
    con.close()
    return [
        {"dialogue_id": r[0], "dialogue_length_messages": r[1], "dialogue_length_chars": r[2]}
        for r in rows
    ]


def fetch_messages(dialogue_id: int) -> list[dict]:
    con = duckdb.connect(str(DB_PATH))
    rows = con.execute(
        "SELECT msg_order, sender_gender, lang, message FROM dialogue WHERE dialogue_id = ? ORDER BY msg_order;",
        [dialogue_id],
    ).fetchall()
    con.close()
    return [{"msg_order": r[0], "sender_gender": r[1], "lang": r[2], "message": r[3]} for r in rows]


def call_grok_translate(messages_batch: list[dict], target_lang: str) -> list[str]:
    """Translate a batch of messages to target_lang. Returns list of translated strings."""
    lang_names = {"ru": "Russian", "en": "English"}
    lang_name = lang_names.get(target_lang, target_lang)

    texts = [m["message"] for m in messages_batch]
    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(texts))

    payload = {
        "model": GROK_MODEL,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    f"You are a professional translator. Your only job is to translate text to {lang_name}.\n"
                    f"You will receive exactly {len(texts)} numbered messages.\n"
                    f"Return a JSON object: {{\"translations\": [\"<translation 1>\", \"<translation 2>\", ...]}}.\n"
                    f"The array MUST have exactly {len(texts)} strings — one per input message, in the same order.\n"
                    "Never merge messages. Never add or remove items. Never add explanations or notes."
                ),
            },
            {
                "role": "user",
                "content": f"Translate exactly these {len(texts)} messages to {lang_name}:\n\n{numbered}",
            },
        ],
    }

    for attempt in range(RETRY_LIMIT):
        try:
            resp = requests.post(
                f"{GROK_BASE_URL.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {GROK_API_KEY}", "Content-Type": "application/json"},
                json=payload,
                timeout=120,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()
            parsed = json.loads(content)
            translations = parsed.get("translations", [])
            if len(translations) == len(texts):
                return [str(t) for t in translations]
            print(f"  [warn] got {len(translations)} translations for {len(texts)} messages, retrying...")
        except Exception as exc:
            print(f"  [error] attempt {attempt+1}: {exc}")
            time.sleep(2 ** attempt)

    # fallback: return originals
    print("  [fallback] returning originals")
    return texts


def translate_dialogue(messages: list[dict], target_lang: str) -> list[dict]:
    result = []
    total = len(messages)
    for start in range(0, total, BATCH_SIZE):
        batch = messages[start : start + BATCH_SIZE]
        end = min(start + BATCH_SIZE, total)
        print(f"    [{target_lang}] messages {start+1}-{end}/{total}...")
        translated_texts = call_grok_translate(batch, target_lang)
        for msg, text in zip(batch, translated_texts):
            result.append({
                "msg_order": msg["msg_order"],
                "sender_gender": msg["sender_gender"],
                "lang": target_lang,
                "message": text,
            })
    return result


def main():
    if not GROK_API_KEY:
        print("ERROR: GROK_API_KEY is not set in .env")
        sys.exit(1)

    # resume support: load existing output if present
    existing_data = {"dialogues": []}
    existing_ids = set()
    if OUTPUT_PATH.exists():
        try:
            existing_data = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
            existing_ids = {d["dialogue_id"] for d in existing_data.get("dialogues", [])}
            print(f"Resuming: {len(existing_ids)} dialogue(s) already done: {existing_ids}")
        except Exception:
            pass

    print("Fetching target dialogues...")
    target = fetch_target_dialogues(3)
    print(f"Found {len(target)} dialogues: {[d['dialogue_id'] for d in target]}")

    output_dialogues = list(existing_data.get("dialogues", []))

    for i, d in enumerate(target):
        did = d["dialogue_id"]
        if did in existing_ids:
            print(f"  Skipping {did} (already translated)")
            continue

        print(f"\n[{i+1}/{len(target)}] dialogue_id={did} ({d['dialogue_length_messages']} messages)...")
        messages_sv = fetch_messages(did)

        print(f"  Translating sv->ru...")
        messages_ru = translate_dialogue(messages_sv, "ru")

        print(f"  Translating sv->en...")
        messages_en = translate_dialogue(messages_sv, "en")

        output_dialogues.append({
            "dialogue_id": did,
            "dialogue_length_messages": d["dialogue_length_messages"],
            "dialogue_length_chars": d["dialogue_length_chars"],
            "messages": {
                "sv": messages_sv,
                "ru": messages_ru,
                "en": messages_en,
            },
        })

        # save after each dialogue for resume support
        OUTPUT_PATH.write_text(
            json.dumps({"dialogues": output_dialogues}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  Saved progress to {OUTPUT_PATH}")

    print(f"\nDone! {len(output_dialogues)} dialogue(s) in {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
