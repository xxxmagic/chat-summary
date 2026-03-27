import requests


def main() -> None:
    base = "http://127.0.0.1:8000"
    did = requests.get(f"{base}/api/dialogues", timeout=10).json()[0]["dialogue_id"]
    requests.post(f"{base}/api/dialogues/{did}/summary/reset", timeout=20)

    steps = 0
    last = None
    while True:
        steps += 1
        response = requests.post(f"{base}/api/dialogues/{did}/summary/next", timeout=120)
        last = response.json()
        if last.get("is_complete") or last.get("status") == "already_complete":
            break
        if steps > 2000:
            break

    print(
        {
            "dialogue_id": did,
            "steps": steps,
            "status": last.get("status") if last else None,
            "processed": last.get("processed_messages") if last else None,
            "total": last.get("total_messages") if last else None,
            "facts": last.get("fact_count") if last else None,
        }
    )


if __name__ == "__main__":
    main()
