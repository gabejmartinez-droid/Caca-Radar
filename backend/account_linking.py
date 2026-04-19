from datetime import datetime, timezone

SOCIAL_PROVIDERS = {"google", "apple"}
SUPPORTED_AUTH_METHODS = {"password", *SOCIAL_PROVIDERS}


def _append_unique(items, value):
    if value and value in SUPPORTED_AUTH_METHODS and value not in items:
        items.append(value)


def normalize_auth_methods(user):
    methods = []

    for method in user.get("auth_methods", []) or []:
        _append_unique(methods, method)

    if user.get("password_hash"):
        _append_unique(methods, "password")

    legacy_provider = user.get("auth_provider")
    if legacy_provider in SOCIAL_PROVIDERS:
        _append_unique(methods, legacy_provider)

    for provider in (user.get("linked_providers") or {}).keys():
        if provider in SOCIAL_PROVIDERS:
            _append_unique(methods, provider)

    return methods


def build_provider_link_updates(user, provider, profile, now=None):
    if provider not in SOCIAL_PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}")

    timestamp = (now or datetime.now(timezone.utc)).isoformat()
    methods = normalize_auth_methods(user)
    _append_unique(methods, provider)

    linked_providers = dict(user.get("linked_providers") or {})
    existing_link = dict(linked_providers.get(provider) or {})
    linked_providers[provider] = {
        **existing_link,
        "email": profile.get("email") or existing_link.get("email"),
        "name": profile.get("name") or existing_link.get("name"),
        "picture": profile.get("picture") or existing_link.get("picture"),
        "subject": profile.get("subject") or existing_link.get("subject"),
        "linked_at": existing_link.get("linked_at") or timestamp,
        "last_login_at": timestamp,
    }

    updates = {
        "auth_methods": methods,
        "linked_providers": linked_providers,
    }

    if not user.get("auth_provider"):
        updates["auth_provider"] = provider

    if profile.get("picture") and not user.get("picture"):
        updates["picture"] = profile["picture"]

    if profile.get("name") and not user.get("name"):
        updates["name"] = profile["name"]

    return updates


def build_password_link_updates(user, password_hash):
    methods = normalize_auth_methods(user)
    _append_unique(methods, "password")

    updates = {
        "password_hash": password_hash,
        "auth_methods": methods,
    }

    if not user.get("auth_provider"):
        updates["auth_provider"] = "password"

    return updates
