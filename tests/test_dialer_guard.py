"""The dial guard must accept only the assessment test line."""

import pytest

from src import config


def test_guard_accepts_target_in_various_formats():
    assert config.assert_dialable("+18054398008") == config.TARGET_NUMBER
    assert config.assert_dialable("+1 (805) 439-8008") == config.TARGET_NUMBER


def test_guard_rejects_any_other_number():
    with pytest.raises(config.ConfigError):
        config.assert_dialable("+19998887777")
    with pytest.raises(config.ConfigError):
        config.assert_dialable("+18054398009")
