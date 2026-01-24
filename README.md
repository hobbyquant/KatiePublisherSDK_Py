# Katie Publisher SDKs

Official SDKs for publishing voice messages to Katie channels.

## Available SDKs

| Language | Status | Directory |
|----------|--------|-----------|
| [Python](./python/) | **Available** | `python/` |

## Overview

Katie Publisher SDKs allow you to integrate voice notifications into your applications. Send text messages to Katie channels, and they'll be converted to speech and delivered to all subscribed devices in real-time.

### Key Features

- **Simple API** - Just `publish()` or `broadcast()`
- **Smart Filtering** - Subscribers filter messages based on metadata
- **Broadcast Mode** - Override filters for critical announcements
- **TTL Support** - Messages expire if not processed in time
- **TTS Optimization** - Separate display text from speech text with `message_tts`

## Installation

### Python

```bash
# Via SSH (for private repo access)
pip install git+ssh://git@github.com/hobby/KatiePublisherSDK.git
```

### Quick Start

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

## Quick Comparison

### Publishing (Filtered)

Messages sent with `publish()` respect subscriber filters:

```python
client.publish("Stock alert", meta={"symbol": "AAPL", "price": 200})
```

### Broadcasting (Unfiltered)

Messages sent with `broadcast()` go to ALL subscribers:

```python
client.broadcast("Emergency: System maintenance in 10 minutes")
```

## API Endpoint

All SDKs communicate with the Katie API:

```
POST /v1/messaging/publish
Content-Type: application/json

{
  "channel_apikey": "your-channel-api-key",
  "message": "Your message here",
  "message_tts": "Your message here",  // optional, TTS-optimized text
  "ttl_seconds": 60,                   // optional
  "meta": {                            // optional
    "key": "value",
    "broadcast": true                  // set by broadcast() method
  }
}
```

## Contributing

We welcome contributions for additional language SDKs. See each SDK's directory for language-specific contribution guidelines.

### Planned SDKs

- **C/C++** - For embedded devices and IoT applications
- **Go** - For high-performance server applications
- **Rust** - For systems programming and WebAssembly

If you'd like to contribute an SDK for another language, please open an issue to discuss.
