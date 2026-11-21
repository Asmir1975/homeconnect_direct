"""Constants."""

from __future__ import annotations

from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "homeconnect_ws"
PLATFORMS: Final = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.SELECT,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.LIGHT,
    Platform.FAN,
]

CONF_PSK: Final = "psk"
CONF_AES_IV: Final = "aes_iv"
CONF_FILE: Final = "file"
CONF_MANUAL_HOST: Final = "manual_host"
CONF_DEV_SETUP_FROM_DUMP: Final = "setup_from_dump_enabled"
CONF_DEV_OVERRIDE_HOST: Final = "override_host"
CONF_DEV_OVERRIDE_PSK: Final = "override_psk"

MAX_RECONECT_TIME: Final = 300

# Backoff for the initial connect loop in the coordinator (seconds). Separate from
# the library's own reconnect backoff, which only covers an already-established session.
INITIAL_CONNECT_BACKOFF: Final = 2
MAX_CONNECT_BACKOFF: Final = 60
# Random share (seconds) added to every wait, so several Home Assistant instances
# and apps do not connect to one appliance in the same moment.
CONNECT_JITTER: Final = 2
# An mDNS announcement of the appliance ends the wait for the next connect attempt, but
# not sooner than this many seconds after the last attempt.
MIN_NUDGE_INTERVAL: Final = 5

CONF_FILTER_UNSAVED_FAVORITES: Final = "filter_unsaved_favorites"
