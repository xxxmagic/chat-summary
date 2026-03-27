import duckdb


def main() -> None:
    con = duckdb.connect("dialogs.duckdb")
    con.execute("PRAGMA threads=4;")

    con.execute(
        """
        CREATE OR REPLACE TABLE dialogue AS
        SELECT
            CAST(id AS BIGINT) AS id,
            CAST(dialogue_id AS BIGINT) AS dialogue_id,
            CAST(msg_order AS INTEGER) AS msg_order,
            sender_gender,
            lang,
            message,
            length(message) AS message_length_chars
        FROM read_csv_auto('dialogue_export.csv', header=true);
        """
    )

    con.execute(
        """
        CREATE OR REPLACE TABLE dialogue_stats AS
        SELECT
            dialogue_id,
            count(*) AS dialogue_length_messages,
            sum(length(message)) AS dialogue_length_chars,
            avg(length(message)) AS avg_message_length_chars
        FROM dialogue
        GROUP BY dialogue_id;
        """
    )

    con.execute(
        """
        CREATE OR REPLACE VIEW dialogue_with_lengths AS
        SELECT
            d.*,
            s.dialogue_length_messages,
            s.dialogue_length_chars,
            s.avg_message_length_chars
        FROM dialogue d
        JOIN dialogue_stats s USING (dialogue_id);
        """
    )

    total_rows = con.execute("SELECT count(*) FROM dialogue").fetchone()[0]
    total_dialogues = con.execute("SELECT count(*) FROM dialogue_stats").fetchone()[0]
    top5 = con.execute(
        """
        SELECT
            dialogue_id,
            dialogue_length_messages,
            dialogue_length_chars,
            round(avg_message_length_chars, 2) AS avg_message_length_chars
        FROM dialogue_stats
        ORDER BY dialogue_length_messages DESC, dialogue_length_chars DESC
        LIMIT 5;
        """
    ).fetchall()

    con.close()
    print(f"rows: {total_rows}")
    print(f"dialogues: {total_dialogues}")
    print("top5 longest dialogues (by message count):")
    for row in top5:
        print(row)


if __name__ == "__main__":
    main()
