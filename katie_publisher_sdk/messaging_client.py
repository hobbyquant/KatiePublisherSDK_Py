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


def _compare_filter(filter_obj: Any, data: dict) -> bool:
    """Evaluate a subscription filter against a data payload.

    Returns True if the data passes the filter (i.e. subscriber would receive).
    This is a local copy of the server-side filter logic so publishers can
    pre-evaluate without a round-trip.
    """
    if isinstance(data, dict) and data.get("broadcast") is True:
        return True
    if not filter_obj or not isinstance(filter_obj, dict):
        return True
    if "rules" not in filter_obj and "field" in filter_obj:
        filter_obj = {"combinator": "and", "rules": [filter_obj]}

    combinator = str(filter_obj.get("combinator") or "and").lower()
    rules = filter_obj.get("rules") or []
    if not isinstance(rules, list) or len(rules) == 0:
        return True

    def to_number(x: Any):
        if isinstance(x, bool):
            return None
        if isinstance(x, (int, float)):
            return float(x)
        if isinstance(x, str):
            s = x.strip()
            if s == "":
                return None
            try:
                if s.isdigit() or (s.startswith("-") and s[1:].isdigit()):
                    return float(int(s))
                return float(s)
            except Exception:
                return None
        return None

    def norm_str(x: Any) -> str:
        return ("" if x is None else str(x)).strip().casefold()

    def is_empty(x: Any) -> bool:
        if x is None:
            return True
        if isinstance(x, str):
            return len(x.strip()) == 0
        try:
            return len(x) == 0
        except Exception:
            return False

    def cmp_atomic(field: str, op: str, target: Any) -> bool:
        val = data.get(field, None)
        op = (op or "==").strip()
        if op == "isEmpty":
            return is_empty(val)
        v_num = to_number(val)
        t_num = to_number(target)
        if op == "in":
            values = target if isinstance(target, list) else [target]
            if v_num is not None and all(to_number(x) is not None for x in values):
                return any(v_num == to_number(x) for x in values)
            v_str = norm_str(val)
            return any(v_str == norm_str(x) for x in values)
        if op == "==":
            if v_num is not None and t_num is not None:
                return v_num == t_num
            return norm_str(val) == norm_str(target)
        if op in (">", ">=", "<", "<="):
            if v_num is not None and t_num is not None:
                if op == ">":  return v_num >  t_num
                if op == ">=": return v_num >= t_num
                if op == "<":  return v_num <  t_num
                if op == "<=": return v_num <= t_num
            v_str, t_str = norm_str(val), norm_str(target)
            if op == ">":  return v_str >  t_str
            if op == ">=": return v_str >= t_str
            if op == "<":  return v_str <  t_str
            if op == "<=": return v_str <= t_str
        if op == "contains":
            return norm_str(target) in norm_str(val)
        if op == "startsWith":
            return norm_str(val).startswith(norm_str(target))
        if op == "endsWith":
            return norm_str(val).endswith(norm_str(target))
        return False

    def eval_rule(rule: Any) -> bool:
        if isinstance(rule, dict) and "rules" in rule and "combinator" in rule:
            return _compare_filter(rule, data)
        if not isinstance(rule, dict):
            return False
        field = rule.get("field")
        op = rule.get("op")
        target = rule.get("value")
        if not field or not op:
            return False
        return cmp_atomic(str(field), str(op), target)

    results = [eval_rule(r) for r in rules]
    if combinator == "or":
        return any(results)
    return all(results)


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
        self._cached_filters: Optional[Dict[str, Any]] = None

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

        payload = {"message": message}

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
                headers={
                    "Authorization": f"Bearer {self.channel_apikey}",
                    "Content-Type": "application/json",
                },
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

    def get_subscriber_filters(self) -> Dict[str, Any]:
        """
        Fetch aggregated subscription filters for this channel.

        Returns the union of filter rules across all subscribers, without
        exposing individual subscriber details. Use this to determine
        whether any subscriber would receive a message with a given meta
        payload before calling ``publish()``.

        The result is cached internally. Call ``refresh_filters()`` to
        update the cache, or pass ``force=True`` to bypass it.

        Returns:
            A dictionary containing:
            - channel_id: The numeric channel ID
            - channel_name: The channel name
            - subscriber_count: Total number of subscriptions
            - has_unfiltered_subscribers: True if any subscription has no filter
            - filters: List of dicts with ``field``, ``op``, and ``value`` keys

        Raises:
            MessagingPublishError: If the request fails

        Example:
            >>> info = client.get_subscriber_filters()
            >>> print(info["subscriber_count"])
            5
            >>> print(info["has_unfiltered_subscribers"])
            False
            >>> for f in info["filters"]:
            ...     print(f"{f['field']} {f['op']} {f['value']}")
        """
        url = f"{self.base_url}/v1/messaging/subscriber-filters"

        try:
            response = requests.get(
                url,
                headers={"Authorization": f"Bearer {self.channel_apikey}"},
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            self._cached_filters = data
            return data
        except requests.exceptions.HTTPError as e:
            try:
                error_detail = e.response.json()
            except Exception:
                error_detail = None
            raise MessagingPublishError(
                f"Failed to fetch subscriber filters: {e}",
                status_code=e.response.status_code if e.response else None,
                response=error_detail,
            ) from e
        except requests.exceptions.RequestException as e:
            raise MessagingPublishError(f"Failed to fetch subscriber filters: {e}") from e

    def refresh_filters(self) -> Dict[str, Any]:
        """Refresh the cached subscriber filters from the API.

        Equivalent to ``get_subscriber_filters()`` but makes the intent
        of refreshing the cache explicit.

        Returns:
            The subscriber filters response (same as ``get_subscriber_filters()``).
        """
        return self.get_subscriber_filters()

    def should_publish(self, meta: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check locally whether any subscriber would receive a message with the
        given *meta* payload.

        Uses the cached result from ``get_subscriber_filters()``. If no cache
        exists yet, it will fetch automatically.

        This lets publishers skip the ``publish()`` call entirely when no
        subscriber's filter would match, saving an API round-trip and TTS
        costs.

        Args:
            meta: The metadata dictionary you intend to publish with.
                  Pass ``None`` or ``{}`` if the message has no metadata.

        Returns:
            True if at least one subscriber would receive the message.
            False if no subscribers exist or all filters would reject it.

        Raises:
            MessagingPublishError: If the initial filter fetch fails.

        Example:
            >>> if client.should_publish(meta={"symbol": "AAPL"}):
            ...     client.publish("AAPL is up 3%", meta={"symbol": "AAPL"})
            ... else:
            ...     print("No matching subscribers, skipping")
        """
        if self._cached_filters is None:
            self.get_subscriber_filters()

        filters_data = self._cached_filters

        # No subscribers at all
        if filters_data["subscriber_count"] == 0:
            return False

        # At least one subscriber with no filter — always receives
        if filters_data["has_unfiltered_subscribers"]:
            return True

        # Evaluate each filter rule-set against the meta.
        # The API returns individual rules flattened from all subscribers.
        # We need to reconstruct per-subscriber filter objects to evaluate
        # correctly, but we don't have per-subscriber grouping. Instead,
        # check if the meta satisfies ANY individual rule — if a subscriber
        # had that rule as their only filter, they'd receive the message.
        # This is a conservative (optimistic) check: it may return True
        # when the actual server-side check would reject, but it will
        # never return False when a subscriber would have received.
        effective_meta = meta or {}
        rules = filters_data.get("filters", [])

        if not rules:
            # No rules and no unfiltered subscribers shouldn't happen,
            # but be safe and allow publishing.
            return True

        for rule in rules:
            filter_obj = {"combinator": "and", "rules": [rule]}
            if _compare_filter(filter_obj, effective_meta):
                return True

        return False
