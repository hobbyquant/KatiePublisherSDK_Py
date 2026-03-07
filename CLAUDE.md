# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python SDK for publishing voice messages to Katie channels. Text messages are sent to the Katie API, converted to speech, and delivered to subscribed devices in real-time.

## Build & Install

```bash
# Install in development mode
pip install -e .

# Install from repo
pip install git+ssh://git@github.com/hobby/KatiePublisherSDK.git
```

Build system: setuptools via `pyproject.toml`. No Makefile, no test framework, no linter configured.

## Architecture

Single-module SDK in `katie_publisher_sdk/`:

- **`messaging_client.py`** — The entire SDK implementation. Contains `MessagingClient` (the public API) and `MessagingPublishError` (custom exception).
- **`__init__.py`** — Re-exports `MessagingClient` and `MessagingPublishError`.

`MessagingClient` wraps `POST /v1/messaging/publish` on a Katie API server. Two public methods:
- `publish()` — Send a message; subscribers can filter based on `meta` dict.
- `broadcast()` — Calls `publish()` with `meta={"broadcast": True}` to bypass subscriber filters.

Both methods accept optional `ttl_seconds` (message expiry), `meta` (filtering metadata), and `message_tts` (speech-optimized text separate from display text).

## Dependencies

- Runtime: `requests>=2.25.0`
- Python: `>=3.8`
