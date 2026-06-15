"""
Kafka 生产者：读取用户行为 CSV，并发送到 Kafka。
"""

import csv
import json
import os
import sys
import time

from kafka import KafkaProducer


KAFKA_BROKER = "localhost:9092"
TOPIC_NAME = "user_behavior"
CSV_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "data", "UserBehavior.csv"
)

DEFAULT_SEND_RATE = 1000
DEFAULT_MAX_MESSAGES = 50000


def read_int_env(name, default):
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        print(f"[ERROR] {name} must be an integer, got: {raw}")
        sys.exit(1)


SEND_RATE = read_int_env("KAFKA_SEND_RATE", DEFAULT_SEND_RATE)
MAX_MESSAGES = read_int_env("KAFKA_MAX_MESSAGES", DEFAULT_MAX_MESSAGES)


def create_producer():
    try:
        return KafkaProducer(
            bootstrap_servers=KAFKA_BROKER,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            acks=1,
            batch_size=16384,
            linger_ms=10,
            request_timeout_ms=5000,
            api_version_auto_timeout_ms=5000,
        )
    except Exception as exc:
        print(f"[ERROR] Failed to connect to Kafka broker {KAFKA_BROKER}: {exc}")
        print("        Make sure Kafka is running and topic user_behavior exists.")
        sys.exit(1)


def main():
    if SEND_RATE <= 0:
        print(f"[ERROR] KAFKA_SEND_RATE must be > 0, got: {SEND_RATE}")
        sys.exit(1)
    if MAX_MESSAGES < 0:
        print(f"[ERROR] KAFKA_MAX_MESSAGES must be >= 0, got: {MAX_MESSAGES}")
        sys.exit(1)

    print("=" * 60)
    print("Kafka Producer: simulated realtime user behavior stream")
    print(f"  Broker:        {KAFKA_BROKER}")
    print(f"  Topic:         {TOPIC_NAME}")
    print(f"  Data file:     {CSV_FILE}")
    print(f"  Send rate:     {SEND_RATE} msg/s")
    print(
        "  Max messages:  all rows"
        if MAX_MESSAGES == 0
        else f"  Max messages:  {MAX_MESSAGES}"
    )
    print("=" * 60)

    if not os.path.exists(CSV_FILE):
        print(f"[ERROR] Data file not found: {CSV_FILE}")
        sys.exit(1)

    producer = create_producer()
    sent_count = 0
    start_time = time.time()

    try:
        with open(CSV_FILE, "r", newline="") as csv_file:
            reader = csv.reader(csv_file)
            for row in reader:
                if len(row) != 5:
                    continue

                message = {
                    "user_id": int(row[0]),
                    "item_id": int(row[1]),
                    "category_id": int(row[2]),
                    "behavior": row[3],
                    "timestamp": int(row[4]),
                }

                producer.send(
                    TOPIC_NAME,
                    key=str(message["user_id"]),
                    value=message,
                )

                sent_count += 1

                if sent_count % SEND_RATE == 0:
                    elapsed = time.time() - start_time
                    actual_rate = sent_count / elapsed if elapsed > 0 else 0
                    print(
                        f"[INFO] sent {sent_count:,} messages | "
                        f"actual rate: {actual_rate:.0f} msg/s"
                    )
                    expected_time = sent_count / SEND_RATE
                    if elapsed < expected_time:
                        time.sleep(expected_time - elapsed)

                if 0 < MAX_MESSAGES <= sent_count:
                    break

        producer.flush()
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user, stopping producer...")
    finally:
        producer.close()
        elapsed = time.time() - start_time
        print(
            f"\n[DONE] sent {sent_count:,} messages in {elapsed:.1f} seconds"
        )


if __name__ == "__main__":
    main()
