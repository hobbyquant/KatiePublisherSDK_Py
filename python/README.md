# Katie Publisher SDK - Python

A Python SDK for publishing voice messages to Katie channels.

## Installation

```bash
pip install git+https://github.com/hobby/KatiePublisherSDK.git
```

## Quick Start

```python
from katie_publisher_sdk import MessagingClient

# Initialize the client
client = MessagingClient(
    base_url="https://katiespeaker.com",
    channel_apikey="your-channel-api-key"
)

# Publish a message (converted to speech and sent to subscribers)
client.publish("Hello, World!")
```

## Features

### Standard Publishing

Publish messages that respect subscriber filters:

```python
# Simple message
client.publish("The meeting starts in 5 minutes")

# Message with TTL (expires after 60 seconds if not processed)
client.publish(
    message="Flash sale ending soon!",
    ttl_seconds=60
)

# Message with metadata (subscribers can filter on these values)
client.publish(
    message="Bitcoin price alert",
    meta={
        "asset": "BTC",
        "price": 50000,
        "direction": "up"
    }
)
```

### Broadcasting

Broadcast messages bypass ALL subscriber filters - use for important announcements:

```python
# Broadcast to everyone (ignores subscriber filters)
client.broadcast("Emergency: System maintenance in 10 minutes")

# Broadcast with metadata
client.broadcast(
    message="Critical security update required",
    ttl_seconds=300,
    meta={"priority": "critical"}
)
```

## Examples

### Clock Publisher

```python
from katie_publisher_sdk import MessagingClient
from datetime import datetime
import pytz
import time

client = MessagingClient(
    base_url="https://katiespeaker.com",
    channel_apikey="your-api-key"
)

tz = pytz.timezone("America/New_York")

while True:
    now = datetime.now(tz)
    message_time = now.strftime("%I:%M %p").lstrip("0")

    # Publish with metadata so subscribers can filter
    # e.g., "only announce on the hour" (minute == 0)
    client.publish(
        message=f"The time is {message_time}",
        ttl_seconds=120,
        meta={
            "hour": now.hour,
            "minute": now.minute,
            "day_of_week": now.strftime("%A"),
        }
    )

    time.sleep(60)
```

### Stock Price Alert

```python
from katie_publisher_sdk import MessagingClient

client = MessagingClient(
    base_url="https://katiespeaker.com",
    channel_apikey="your-api-key"
)

def on_price_change(symbol, price, change_pct):
    if abs(change_pct) > 5:
        # Major move - broadcast to everyone
        client.broadcast(
            f"{symbol} moved {change_pct:.1f}% to ${price:.2f}"
        )
    else:
        # Normal update - let subscribers filter
        client.publish(
            f"{symbol} is now ${price:.2f}",
            meta={
                "symbol": symbol,
                "price": price,
                "change_pct": change_pct
            }
        )
```

### Error Handling

```python
from katie_publisher_sdk import MessagingClient, MessagingPublishError

client = MessagingClient(
    base_url="https://katiespeaker.com",
    channel_apikey="your-api-key"
)

try:
    client.publish("Hello, World!")
except MessagingPublishError as e:
    print(f"Failed to publish: {e}")
    if e.status_code:
        print(f"HTTP status: {e.status_code}")
    if e.response:
        print(f"Error details: {e.response}")
```

## API Reference

### `MessagingClient`

#### `__init__(base_url, channel_apikey, timeout=10)`

Initialize the messaging client.

| Parameter | Type | Description |
|-----------|------|-------------|
| `base_url` | str | The base URL of the Katie API (e.g., "https://katiespeaker.com") |
| `channel_apikey` | str | Your channel API key |
| `timeout` | int | Request timeout in seconds (default: 10) |

#### `publish(message, ttl_seconds=None, meta=None)`

Publish a message to subscribers. Subscribers can filter based on `meta` values.

| Parameter | Type | Description |
|-----------|------|-------------|
| `message` | str | The message content (converted to speech) |
| `ttl_seconds` | int | Time-to-live in seconds (optional) |
| `meta` | dict | Metadata for filtering (optional) |

**Returns:** `dict` with `message_id` and `channel`

**Raises:** `MessagingPublishError` on failure

#### `broadcast(message, ttl_seconds=None, meta=None)`

Broadcast a message to ALL subscribers, bypassing their filters.

| Parameter | Type | Description |
|-----------|------|-------------|
| `message` | str | The message content (converted to speech) |
| `ttl_seconds` | int | Time-to-live in seconds (optional) |
| `meta` | dict | Additional metadata (optional, `broadcast: true` added automatically) |

**Returns:** `dict` with `message_id` and `channel`

**Raises:** `MessagingPublishError` on failure

### Exceptions

#### `MessagingPublishError`

Raised when message publishing fails.

| Attribute | Type | Description |
|-----------|------|-------------|
| `status_code` | int | HTTP status code (if available) |
| `response` | dict | Error response body (if available) |

## Understanding Filters vs Broadcasts

| Method | Who receives it? | Use case |
|--------|-----------------|----------|
| `publish()` | Only subscribers whose filters match the `meta` | Regular updates, personalized alerts |
| `broadcast()` | ALL subscribers, regardless of filters | Emergency alerts, critical announcements |

**Example:**
- A clock channel publishes time every minute with `meta={"minute": 30}`
- Subscriber A filters for `minute == 0` (hourly) -> only hears on the hour
- Subscriber B has no filter -> hears every minute
- If you call `broadcast("Emergency!")` -> BOTH subscribers hear it
