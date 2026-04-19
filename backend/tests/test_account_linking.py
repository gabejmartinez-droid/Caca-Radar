from account_linking import (
    build_password_link_updates,
    build_provider_link_updates,
    normalize_auth_methods,
)


def test_normalize_auth_methods_includes_password_and_legacy_provider():
    user = {
        "password_hash": "hashed",
        "auth_provider": "google",
    }

    assert normalize_auth_methods(user) == ["password", "google"]


def test_build_provider_link_updates_links_existing_password_user():
    user = {
        "email": "person@example.com",
        "password_hash": "hashed",
        "auth_provider": "password",
        "auth_methods": ["password"],
        "linked_providers": {},
    }

    updates = build_provider_link_updates(
        user,
        "google",
        {
            "email": "person@example.com",
            "name": "Person Example",
            "picture": "https://example.com/avatar.png",
            "subject": "google-sub-123",
        },
    )

    assert updates["auth_methods"] == ["password", "google"]
    assert updates["linked_providers"]["google"]["email"] == "person@example.com"
    assert updates["linked_providers"]["google"]["subject"] == "google-sub-123"


def test_build_password_link_updates_adds_password_to_social_account():
    user = {
        "email": "person@example.com",
        "password_hash": "",
        "auth_provider": "google",
        "auth_methods": ["google"],
        "linked_providers": {"google": {"email": "person@example.com"}},
    }

    updates = build_password_link_updates(user, "new-hash")

    assert updates["password_hash"] == "new-hash"
    assert updates["auth_methods"] == ["google", "password"]
