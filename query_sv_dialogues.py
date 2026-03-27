import duckdb


def main() -> None:
    con = duckdb.connect(r"E:\_Projects\Summary\dialogs.duckdb")
    query = """
    SELECT
        d.dialogue_id,
        d.msg_order,
        d.sender_gender,
        d.lang,
        d.message,
        s.dialogue_length_messages
    FROM dialogue d
    JOIN dialogue_stats s USING (dialogue_id)
    WHERE d.lang = 'sv'
      AND s.dialogue_length_messages > 100
    QUALIFY row_number() OVER (PARTITION BY d.dialogue_id ORDER BY d.msg_order) = 1
    ORDER BY s.dialogue_length_messages DESC, d.dialogue_id
    LIMIT 5;
    """
    rows = con.execute(query).fetchall()
    con.close()

    print(f"count: {len(rows)}")
    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
