"""
Katie Messaging Publisher SDK

A simple SDK for publishing messages to Katie channels.
"""

import requests
from typing import Optional, Dict, Any


class MessagingPublishError(Exception):
    """Exception raised when message publishing fails."""

    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class MessagingClient:
    """
    Client for publishing messages to Katie channels.

    Example:
        >>> client = MessagingClient(
        ...     base_url="https://katiespeaker.com",
        ...     channel_apikey="your-api-key"
        ... )
        >>> client.publish("Hello, world!")
        {'message_id': '...', 'channel': '...'}
    """

    def __init__(self, base_url: str, channel_apikey: str, timeout: int = 10):
        """
        Initialize the messaging client.

        Args:
            base_url: The base URL of the Katie API (e.g., "https://katiespeaker.com")
            channel_apikey: The API key for your channel
            timeout: Request timeout in seconds (default: 10)
        """
        self.base_url = base_url.rstrip('/')
        self.channel_apikey = channel_apikey
        self.timeout = timeout

    def publish(
        self,
        message: str,
        ttl_seconds: Optional[int] = None,
        meta: Optional[Dict[str, Any]] = None,
        message_tts: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Publish a message to the channel.

        Messages are converted to speech and delivered to all subscribed devices.
        Subscribers can filter messages based on the `meta` dictionary.

        Args:
            message: The message content to publish (used for display)
            ttl_seconds: Time-to-live in seconds. Message expires if not processed
                         within this time. (optional)
            meta: Additional metadata dictionary. Subscribers can filter based on
                  these values. (optional)
            message_tts: TTS-optimized message text. If provided, this text is used
                         for speech synthesis instead of `message`. Useful when the
                         display text differs from how it should be spoken. (optional)

        Returns:
            The response from the API as a dictionary containing:
            - message_id: Unique identifier for the published message
            - channel: The channel ID the message was published to

        Raises:
            MessagingPublishError: If the publish request fails

        Example:
            >>> client.publish(
            ...     message="The time is 3:30 PM",
            ...     ttl_seconds=60,
            ...     meta={"hour": 15, "minute": 30}
            ... )
            >>> # With TTS-optimized text
            >>> client.publish(
            ...     message="AAPL: $150.25 (+2.5%)",
            ...     message_tts="Apple stock is at 150 dollars and 25 cents, up 2.5 percent"
            ... )
        """
        url = f"{self.base_url}/v1/messaging/publish"

        payload = {
            "channel_apikey": self.channel_apikey,
            "message": message,
        }

        if ttl_seconds is not None:
            payload["ttl_seconds"] = ttl_seconds

        if meta is not None:
            payload["meta"] = meta

        if message_tts is not None:
            payload["message_tts"] = message_tts

        try:
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            try:
                error_detail = e.response.json()
            except Exception:
                error_detail = None
            raise MessagingPublishError(
                f"Failed to publish message: {e}",
                status_code=e.response.status_code if e.response else None,
                response=error_detail
            ) from e
        except requests.exceptions.RequestException as e:
            raise MessagingPublishError(f"Failed to publish message: {e}") from e

    def broadcast(
        self,
        message: str,
        ttl_seconds: Optional[int] = None,
        meta: Optional[Dict[str, Any]] = None,
        message_tts: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Broadcast a message to ALL subscribers, bypassing their filters.

        Use this for important announcements that should reach everyone,
        regardless of their subscription filter settings.

        Args:
            message: The message content to broadcast (used for display)
            ttl_seconds: Time-to-live in seconds. (optional)
            meta: Additional metadata dictionary. The broadcast flag will be
                  automatically added. (optional)
            message_tts: TTS-optimized message text. If provided, this text is used
                         for speech synthesis instead of `message`. (optional)

        Returns:
            The response from the API as a dictionary

        Raises:
            MessagingPublishError: If the broadcast request fails

        Example:
            >>> client.broadcast("Emergency: Building evacuation required")
            >>> client.broadcast(
            ...     message="System maintenance in 10 minutes",
            ...     ttl_seconds=600
            ... )
        """
        broadcast_meta = {"broadcast": True}
        if meta:
            broadcast_meta.update(meta)

        return self.publish(
            message=message,
            ttl_seconds=ttl_seconds,
            meta=broadcast_meta,
            message_tts=message_tts
        )
