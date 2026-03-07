# katie-publisher-sdk

Python SDK for publishing voice messages to Katie channels. Text messages are sent to the Katie API, converted to speech, and delivered to subscribed devices in real-time.

## Installation

```bash
pip install katie-publisher-sdk
```

Requires Python >= 3.8.

## Quick Start

```python
from katie_publisher_sdk import MessagingClient

client = MessagingClient(
    base_url="https://katiespeaker.com",
    channel_apikey="your-channel-api-key"
)

# Publish a message (converted to speech and sent to subscribers)
client.publish("Hello, World!")

# Broadcast to ALL subscribers (bypasses filters)
client.broadcast("Emergency announcement")
```

## SDK Reference

### `MessagingClient(base_url, channel_apikey, timeout=10)`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `base_url` | `str` | Yes | — | Base URL of the Katie API (e.g., `"https://katiespeaker.com"`) |
| `channel_apikey` | `str` | Yes | — | API key for your channel |
| `timeout` | `int` | No | `10` | Request timeout in seconds |

### `client.publish(message, ttl_seconds=None, meta=None, message_tts=None)`

Send a message to the channel. Subscribers can filter messages based on the `meta` dictionary.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `message` | `str` | Yes | — | Message content (used for display) |
| `ttl_seconds` | `int` | No | `None` | Time-to-live in seconds; message expires if not processed in time |
| `meta` | `dict` | No | `None` | Metadata dict; subscribers can filter based on these values |
| `message_tts` | `str` | No | `None` | TTS-optimized text used for speech synthesis instead of `message` |

**Returns:** `dict` with `message_id` (unique identifier) and `channel` (channel ID).

**Raises:** `MessagingPublishError` on failure.

### `client.broadcast(message, ttl_seconds=None, meta=None, message_tts=None)`

Broadcast a message to **all** subscribers, bypassing their filter settings. Automatically sets `meta["broadcast"] = True` (merged with any `meta` you provide).

Parameters, return value, and exceptions are the same as `publish()`.

### `client.get_subscriber_filters()`

Fetch aggregated subscription filters for this channel. Returns the union of filter rules across all subscribers without exposing individual subscriber details. The result is cached internally for use by `should_publish()`.

**Returns:** `dict` with:

| Field | Type | Description |
|-------|------|-------------|
| `channel_id` | `int` | Numeric channel ID |
| `channel_name` | `str` | Channel name |
| `subscriber_count` | `int` | Total number of subscriptions |
| `has_unfiltered_subscribers` | `bool` | `True` if any subscription has no filter (always receives) |
| `filters` | `list[dict]` | Deduplicated filter rules with `field`, `op`, and `value` keys |

**Raises:** `MessagingPublishError` on failure.

### `client.refresh_filters()`

Re-fetch subscriber filters from the API and update the internal cache. Equivalent to `get_subscriber_filters()`.

### `client.should_publish(meta=None)`

Check locally whether any subscriber would receive a message with the given `meta` payload. Uses the cached result from `get_subscriber_filters()` (auto-fetches on first call).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `meta` | `dict` | No | `None` | The metadata you intend to publish with |

**Returns:** `True` if at least one subscriber would receive the message, `False` otherwise.

**Note:** This is a conservative (optimistic) check. It may return `True` when the server would reject (because per-subscriber filter grouping is not exposed), but it will never return `False` when a subscriber would have received. This means you won't accidentally skip messages that should be delivered.

**Raises:** `MessagingPublishError` if the initial filter fetch fails.

### `MessagingPublishError`

Raised when a publish or broadcast request fails.

| Attribute | Type | Description |
|-----------|------|-------------|
| `status_code` | `int` or `None` | HTTP status code (if available) |
| `response` | `dict` or `None` | Parsed error response body (if available) |

## Usage Examples

### Basic publish

```python
client.publish("The weekly report is ready.")
```

### Publish with metadata (subscriber filtering)

```python
client.publish(
    "AAPL is up 3% today",
    meta={"symbol": "AAPL", "category": "stocks"}
)
```

Subscribers who filter on `symbol=AAPL` will receive this message; others won't.

### Broadcast (critical announcements)

```python
client.broadcast("Emergency: Building evacuation required")
```

All subscribers receive the message regardless of their filter settings.

### TTS-optimized text

When the display text differs from how it should be spoken:

```python
client.publish(
    message="AAPL: $150.25 (+2.5%)",
    message_tts="Apple stock is at 150 dollars and 25 cents, up 2.5 percent"
)
```

### TTL (message expiry)

```python
client.publish(
    "The time is 3:30 PM",
    ttl_seconds=60
)
```

The message expires after 60 seconds if not processed.

### Smart publishing (skip when no subscribers match)

```python
# Fetch filters once at startup
client.get_subscriber_filters()

# Before each publish, check locally if anyone would receive it
meta = {"symbol": "AAPL", "category": "stocks"}
if client.should_publish(meta=meta):
    client.publish("AAPL is up 3%", meta=meta)
else:
    print("No matching subscribers, skipping")
```

### Inspect subscriber filters

```python
info = client.get_subscriber_filters()
print(f"Subscribers: {info['subscriber_count']}")
print(f"Unfiltered: {info['has_unfiltered_subscribers']}")
for f in info["filters"]:
    print(f"  {f['field']} {f['op']} {f['value']}")
```

### Periodic filter refresh (long-running publishers)

```python
import time

client.get_subscriber_filters()  # initial fetch

while True:
    meta = get_current_meta()
    if client.should_publish(meta=meta):
        client.publish(build_message(), meta=meta)

    # Refresh filters periodically (e.g., every 5 minutes)
    if time_to_refresh():
        client.refresh_filters()

    time.sleep(60)
```

### Error handling

```python
from katie_publisher_sdk import MessagingClient, MessagingPublishError

client = MessagingClient(
    base_url="https://katiespeaker.com",
    channel_apikey="your-channel-api-key"
)

try:
    client.publish("Hello!")
except MessagingPublishError as e:
    print(f"Publish failed: {e}")
    if e.status_code:
        print(f"HTTP status: {e.status_code}")
    if e.response:
        print(f"Error detail: {e.response}")
```

## API Endpoints

The SDK wraps the following endpoints:

### `POST /v1/messaging/publish`

Publish a message for TTS conversion and delivery.

**Request body:**
```json
{
  "channel_apikey": "your-channel-api-key",
  "message": "Your message here",
  "message_tts": "TTS-optimized text",
  "ttl_seconds": 60,
  "meta": {
    "key": "value",
    "broadcast": true
  }
}
```

Only `channel_apikey` and `message` are required. All other fields are optional.

**Response body:**
```json
{
  "message_id": "unique-message-id",
  "channel": "channel-id"
}
```

### `GET /v1/messaging/subscriber-filters?channel_apikey=...`

Fetch aggregated subscription filters for the channel.

**Response body:**
```json
{
  "channel_id": 42,
  "channel_name": "Stock Alerts",
  "subscriber_count": 5,
  "has_unfiltered_subscribers": false,
  "filters": [
    {"field": "symbol", "op": "==", "value": "AAPL"},
    {"field": "delivery_hour", "op": ">=", "value": 9}
  ]
}
```
