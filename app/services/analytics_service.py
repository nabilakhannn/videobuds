"""PostHog analytics wrapper. Fails silently when PostHog is not configured."""

_posthog = None


def init_posthog(api_key, host="https://app.posthog.com"):
    """
    Initialize the PostHog client.

    Args:
        api_key: PostHog project API key. If empty/None, analytics are disabled.
        host: PostHog instance host URL.
    """
    global _posthog
    if not api_key:
        _posthog = None
        return
    try:
        import posthog
        posthog.project_api_key = api_key
        posthog.host = host
        _posthog = posthog
    except Exception:
        _posthog = None


def track(user_id, event_name, properties=None):
    """
    Capture an analytics event.

    Args:
        user_id: Unique user identifier (str or int).
        event_name: Event name (e.g. "campaign_created", "image_generated").
        properties: Optional dict of event properties.
    """
    if _posthog is None:
        return
    try:
        _posthog.capture(
            distinct_id=str(user_id),
            event=event_name,
            properties=properties or {},
        )
    except Exception:
        pass


def identify(user_id, traits):
    """
    Identify a user with a set of traits.

    Args:
        user_id: Unique user identifier (str or int).
        traits: Dict of user properties (e.g. {"email": "...", "plan": "pro"}).
    """
    if _posthog is None:
        return
    try:
        _posthog.identify(
            distinct_id=str(user_id),
            properties=traits or {},
        )
    except Exception:
        pass
