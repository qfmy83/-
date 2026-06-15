"""
Kafka 消费者：消费 user_behavior 主题的数据，并按批次写入 HDFS。
"""

import json
import os
import subprocess
import sys
import tempfile
import time

from kafka import KafkaConsumer


KAFKA_BROKER = "localhost:9092"
TOPIC_NAME = "user_behavior"
HDFS_OUTPUT_PATH = "/data/kafka_output"

DEFAULT_GROUP_ID = "hdfs_writer_group"
DEFAULT_AUTO_OFFSET_RESET = "latest"
DEFAULT_BATCH_SIZE = 5000
DEFAULT_MAX_MESSAGES = 0
DEFAULT_IDLE_FLUSH_SECONDS = 10
WAIT_LOG_SECONDS = 30
ASSIGNMENT_TIMEOUT_SECONDS = 15


def read_int_env(name, default):
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        print(f"[ERROR] {name} must be an integer, got: {raw}")
        sys.exit(1)


def configure_output():
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(line_buffering=True)


BATCH_SIZE = read_int_env("KAFKA_CONSUMER_BATCH_SIZE", DEFAULT_BATCH_SIZE)
MAX_MESSAGES = read_int_env("KAFKA_CONSUMER_MAX_MESSAGES", DEFAULT_MAX_MESSAGES)
GROUP_ID = os.getenv("KAFKA_CONSUMER_GROUP_ID", DEFAULT_GROUP_ID)
AUTO_OFFSET_RESET = os.getenv(
    "KAFKA_CONSUMER_AUTO_OFFSET_RESET",
    DEFAULT_AUTO_OFFSET_RESET,
)
IDLE_FLUSH_SECONDS = read_int_env(
    "KAFKA_CONSUMER_IDLE_FLUSH_SECONDS",
    DEFAULT_IDLE_FLUSH_SECONDS,
)


def run_command(args):
    return subprocess.run(args, capture_output=True, text=True)


def ensure_hdfs_output_path():
    result = run_command(["hdfs", "dfs", "-mkdir", "-p", HDFS_OUTPUT_PATH])
    if result.returncode != 0:
        print(f"[ERROR] Failed to create HDFS path {HDFS_OUTPUT_PATH}")
        print(result.stderr.strip())
        sys.exit(1)


def write_to_hdfs(records, batch_num):
    if not records:
        return

    lines = [
        (
            f"{record['user_id']},{record['item_id']},"
            f"{record['category_id']},{record['behavior']},{record['timestamp']}"
        )
        for record in records
    ]

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        prefix=f"kafka_batch_{batch_num:06d}_",
        suffix=".csv",
        delete=False,
    ) as tmp_file:
        tmp_file.write("\n".join(lines) + "\n")
        tmp_path = tmp_file.name

    hdfs_file = f"{HDFS_OUTPUT_PATH}/batch_{batch_num:06d}.csv"
    try:
        result = run_command(["hdfs", "dfs", "-put", "-f", tmp_path, hdfs_file])
        if result.returncode == 0:
            print(f"[INFO] wrote HDFS: {hdfs_file} ({len(records)} rows)")
        else:
            print(f"[ERROR] failed to write HDFS: {hdfs_file}")
            print(result.stderr.strip())
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def create_consumer():
    try:
        return KafkaConsumer(
            TOPIC_NAME,
            bootstrap_servers=KAFKA_BROKER,
            group_id=GROUP_ID,
            value_deserializer=lambda message: json.loads(message.decode("utf-8")),
            auto_offset_reset=AUTO_OFFSET_RESET,
            enable_auto_commit=True,
            api_version_auto_timeout_ms=5000,
        )
    except Exception as exc:
        print(f"[ERROR] Failed to connect to Kafka broker {KAFKA_BROKER}: {exc}")
        print("        Make sure Kafka is running and topic user_behavior exists.")
        sys.exit(1)


def merge_polled_records(target, source):
    for topic_partition, messages in source.items():
        if not messages:
            continue
        target.setdefault(topic_partition, []).extend(messages)


def wait_for_assignment(consumer):
    print("[INFO] Connecting to Kafka and waiting for partition assignment...")
    deadline = time.time() + ASSIGNMENT_TIMEOUT_SECONDS
    initial_records = {}

    while time.time() < deadline:
        polled = consumer.poll(timeout_ms=1000)
        merge_polled_records(initial_records, polled)

        assignment = consumer.assignment()
        if assignment:
            partitions = ", ".join(
                f"{topic_partition.topic}-{topic_partition.partition}"
                for topic_partition in sorted(
                    assignment,
                    key=lambda item: (item.topic, item.partition),
                )
            )
            print(f"[INFO] Consumer ready. Assigned partitions: {partitions}")
            print("[INFO] You can start Producer now.")
            return initial_records

    print(
        "[WARN] Consumer has not received partition assignment after "
        f"{ASSIGNMENT_TIMEOUT_SECONDS} seconds."
    )
    print("[WARN] Check Kafka broker / topic status before starting Producer.")
    print(
        "[WARN] With auto_offset_reset=latest, messages sent before assignment "
        "may be skipped."
    )
    return initial_records


def process_polled_records(polled, batch, batch_num, total_consumed, last_message_time):
    stop_after_limit = False

    for messages in polled.values():
        for message in messages:
            batch.append(message.value)
            total_consumed += 1
            last_message_time = time.time()

            if len(batch) >= BATCH_SIZE:
                batch_num += 1
                write_to_hdfs(batch, batch_num)
                batch = []

            if 0 < MAX_MESSAGES <= total_consumed:
                stop_after_limit = True
                break
        if stop_after_limit:
            break

    return batch, batch_num, total_consumed, last_message_time, stop_after_limit


def main():
    configure_output()

    if BATCH_SIZE <= 0:
        print(f"[ERROR] KAFKA_CONSUMER_BATCH_SIZE must be > 0, got: {BATCH_SIZE}")
        sys.exit(1)
    if MAX_MESSAGES < 0:
        print(f"[ERROR] KAFKA_CONSUMER_MAX_MESSAGES must be >= 0, got: {MAX_MESSAGES}")
        sys.exit(1)
    if IDLE_FLUSH_SECONDS < 0:
        print(
            "[ERROR] KAFKA_CONSUMER_IDLE_FLUSH_SECONDS must be >= 0, "
            f"got: {IDLE_FLUSH_SECONDS}"
        )
        sys.exit(1)
    if AUTO_OFFSET_RESET not in {"earliest", "latest"}:
        print(
            "[ERROR] KAFKA_CONSUMER_AUTO_OFFSET_RESET must be earliest or latest, "
            f"got: {AUTO_OFFSET_RESET}"
        )
        sys.exit(1)

    print("=" * 60)
    print("Kafka Consumer: write user_behavior stream to HDFS")
    print(f"  Broker:        {KAFKA_BROKER}")
    print(f"  Topic:         {TOPIC_NAME}")
    print(f"  Group:         {GROUP_ID}")
    print(f"  Offset reset:  {AUTO_OFFSET_RESET}")
    print(f"  HDFS path:     {HDFS_OUTPUT_PATH}")
    print(f"  Batch size:    {BATCH_SIZE}")
    print(
        "  Max messages:  unlimited"
        if MAX_MESSAGES == 0
        else f"  Max messages:  {MAX_MESSAGES}"
    )
    print("=" * 60)

    ensure_hdfs_output_path()
    consumer = create_consumer()
    initial_records = wait_for_assignment(consumer)

    batch = []
    batch_num = 0
    total_consumed = 0
    last_message_time = time.time()
    last_wait_log_time = 0
    stop_after_limit = False

    print("[INFO] Consumer started. Waiting for Kafka messages...")
    print("[INFO] Press Ctrl+C to stop; remaining records will be flushed.")

    try:
        while True:
            if initial_records is not None:
                polled = initial_records
                initial_records = None
            else:
                polled = consumer.poll(timeout_ms=1000, max_records=BATCH_SIZE)

            if not polled:
                now = time.time()
                if (
                    batch
                    and IDLE_FLUSH_SECONDS > 0
                    and now - last_message_time >= IDLE_FLUSH_SECONDS
                ):
                    batch_num += 1
                    write_to_hdfs(batch, batch_num)
                    batch = []

                if now - last_wait_log_time >= WAIT_LOG_SECONDS:
                    print("[INFO] waiting for new Kafka messages...")
                    last_wait_log_time = now
                continue

            (
                batch,
                batch_num,
                total_consumed,
                last_message_time,
                stop_after_limit,
            ) = process_polled_records(
                polled,
                batch,
                batch_num,
                total_consumed,
                last_message_time,
            )

            if stop_after_limit:
                print("[INFO] Max message limit reached, stopping consumer...")
                break

    except KeyboardInterrupt:
        print("\n[INFO] Stopping consumer...")
    finally:
        if batch:
            batch_num += 1
            write_to_hdfs(batch, batch_num)
        consumer.close()
        print(
            f"[DONE] consumed {total_consumed:,} messages, "
            f"wrote {batch_num} HDFS batch files"
        )


if __name__ == "__main__":
    main()
