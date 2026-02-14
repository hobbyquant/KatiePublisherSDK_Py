# katie-publisher-sdk

Python SDK for publishing voice messages to Katie channels. Text messages are sent to the Katie API, converted to speech, and delivered to subscribed devices in real-time.

## Installation

```bash
pip install git+ssh://git@github.com/hobby/KatiePublisherSDK.git
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

## API Endpoint

The SDK wraps a single endpoint:

```
POST /v1/messaging/publish
```

### Request body

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

### Response body

```json
{
  "message_id": "unique-message-id",
  "channel": "channel-id"
}
```
