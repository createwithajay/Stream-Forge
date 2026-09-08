from datetime import datetime, timezone

WINDOW_SECONDS = 5 * 60


def get_window_start(timestamp):
    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    epoch_seconds = int(dt.timestamp())
    window_seconds = (epoch_seconds // WINDOW_SECONDS) * WINDOW_SECONDS
    return datetime.fromtimestamp(window_seconds, tz=timezone.utc).isoformat().replace("+00:00", "Z")


test_timestamps = [
    "2026-08-12T08:00:00Z",
    "2026-08-12T08:04:59Z",
    "2026-08-12T08:05:00Z",
    "2026-08-12T08:09:59Z",
    "2026-08-12T08:10:00Z",
]

for timestamp in test_timestamps:
    print(timestamp, "->", get_window_start(timestamp))
