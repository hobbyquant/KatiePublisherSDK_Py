# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Katie Publisher SDK provides client libraries for publishing voice messages to Katie channels. Messages are sent to the Katie API, converted to speech, and delivered to subscribed devices in real-time.

Currently available: **Python SDK**. JavaScript/TypeScript SDK is planned but not yet implemented.

## Build & Install Commands

```bash
# Install in development mode
pip install -e .

# Install from GitHub
pip install git+ssh://git@github.com/hobby/KatiePublisherSDK.git

# Build distribution
python -m build
```

## Architecture

### Python SDK (`katie_publisher_sdk/`)

Single-module SDK with two classes:
- `MessagingClient` - Main client for publishing messages
- `MessagingPublishError` - Exception for publish failures

The SDK wraps a single REST endpoint: `POST /v1/messaging/publish`

### Key Concepts

- **publish()** - Send messages that respect subscriber filters based on `meta` values
- **broadcast()** - Send messages to ALL subscribers, bypassing filters (uses `meta.broadcast=true`)
- **TTL** - Optional time-to-live for message expiration
- **message_tts** - Optional TTS-optimized text (defaults to `message` if not provided)

### API Payload Structure

```json
{
  "channel_apikey": "...",
  "message": "...",
  "message_tts": "...",
  "ttl_seconds": 60,
  "meta": {"key": "value", "broadcast": true}
}
```

## Dependencies

Python SDK requires only `requests>=2.25.0` (Python 3.8+).
