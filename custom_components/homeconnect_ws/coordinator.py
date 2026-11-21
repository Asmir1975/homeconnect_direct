"""Home Connect Coordinator."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import random
import time
from copy import deepcopy
from typing import TYPE_CHECKING

from aiohttp import WSServerHandshakeError
from homeassistant.const import CONF_DESCRIPTION, CONF_DEVICE_ID, CONF_HOST
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeconnect_websocket import (
    AllreadyConnectedError,
    ConnectionFailedError,
    ConnectionState,
    HCHandshakeError,
    HomeAppliance,
)

from .const import (
    CONF_AES_IV,
    CONF_PSK,
    CONNECT_JITTER,
    INITIAL_CONNECT_BACKOFF,
    MAX_CONNECT_BACKOFF,
    MAX_RECONECT_TIME,
    MIN_NUDGE_INTERVAL,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from . import HCConfigEntry

_LOGGER = logging.getLogger(__name__)


class HomeConnectCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    config_entry: HCConfigEntry
    appliance: HomeAppliance
    _connecting: bool = True
    _reconnecting: bool = False
    _reconnect_timer: asyncio.TimerHandle | None = None
    connected: bool = False
    _wake_connect: asyncio.Event | None = None
    _last_connect_attempt: float = 0.0

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: HCConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name=config_entry.data["description"]["info"]["vib"],
            config_entry=config_entry,
            always_update=True,
        )
        self.appliance = HomeAppliance(
            description=deepcopy(config_entry.data[CONF_DESCRIPTION]),
            host=config_entry.data[CONF_HOST],
            app_name="Homeassistant",
            app_id=config_entry.data[CONF_DEVICE_ID],
            psk64=config_entry.data[CONF_PSK],
            iv64=config_entry.data.get(CONF_AES_IV, None),
            connection_callback=self._connection_state_callback,
        )
        self.disconnect_time = time.time()
        if not self.appliance.info:
            msg = "Appliance has no device info"
            raise ConfigEntryError(msg)

    async def close(self) -> None:
        self._connecting = False
        if self._wake_connect is not None:
            self._wake_connect.set()
        self._cancel_reconnect_timer()
        await self.appliance.close()

    async def _async_setup(self) -> None:
        self.config_entry.async_create_background_task(
            self.hass, self._connect(), f"homeconnect_ws_{self.name}"
        )

    async def _connect(self) -> None:
        self.logger.debug(
            "Connecting to %s", self.config_entry.data[CONF_DESCRIPTION]["info"].get("vib")
        )
        first_failure = True
        backoff = INITIAL_CONNECT_BACKOFF
        self._wake_connect = asyncio.Event()
        while self._connecting:
            self._last_connect_attempt = time.monotonic()
            try:
                await self.appliance.connect()
                if self.appliance.session.connected:
                    self.connected = True
                    self.async_set_updated_data(None)
                    return
            except (ConnectionFailedError, HCHandshakeError, WSServerHandshakeError) as err:
                await self.appliance.close()
                msg = f"Can't connect to {self.config_entry.data[CONF_HOST]}, retrying ({err!r})"
                if first_failure:
                    msg = f"{msg}. A short power cycle of the appliance can help."
                    self.logger.error(msg)  # noqa: TRY400
                    first_failure = False  # first_failure_fix
                else:
                    self.logger.debug(msg)
            except AllreadyConnectedError:
                await self.appliance.close()
                msg = f"Allready connected to {self.config_entry.data[CONF_HOST]}"
                self.logger.error(msg)  # noqa: TRY400
                return
            except Exception:
                await self.appliance.close()
                msg = f"Can't connect to {self.config_entry.data[CONF_HOST]}"
                self.logger.exception(msg)
            # Wait before the next attempt so an unreachable device does not cause a
            # tight connect/close loop. Skip the wait if close() ended the loop.
            if self._connecting:
                await self._wait_before_retry(backoff + random.uniform(0, CONNECT_JITTER))  # noqa: S311
                backoff = min(backoff * 2, MAX_CONNECT_BACKOFF)

    async def _wait_before_retry(self, delay: float) -> None:
        """Wait for the next connect attempt, ends early when the appliance announces itself."""
        if self._wake_connect is None:
            await asyncio.sleep(delay)
            return
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(self._wake_connect.wait(), delay)
        self._wake_connect.clear()

    def nudge_connect(self) -> None:
        """Retry the connect now, called when the appliance shows up in mDNS again."""
        if (
            self._wake_connect is not None
            and not self.connected
            and time.monotonic() - self._last_connect_attempt >= MIN_NUDGE_INTERVAL
        ):
            self._wake_connect.set()

    async def _async_update_data(self) -> None:
        return None

    async def _connection_state_callback(self, event: ConnectionState) -> None:
        if event == ConnectionState.RECONNECTING:
            if not self._reconnecting:
                self._reconnecting = True
                reconnect_timeout = int(self.hass.loop.time()) + MAX_RECONECT_TIME
                self._reconnect_timer = self.hass.loop.call_at(
                    reconnect_timeout, self._connection_reconnect_callback
                )

        elif event == ConnectionState.CONNECTED:
            self.connected = True
            if self._reconnecting:
                self.logger.debug(
                    "Reconnected to %s",
                    self.config_entry.data[CONF_DESCRIPTION]["info"].get("vib"),
                )
                self._reconnecting = False
            self._cancel_reconnect_timer()

        elif event == ConnectionState.CLOSED:
            self.connected = False
            self._cancel_reconnect_timer()

        self.async_set_updated_data(None)

    def _cancel_reconnect_timer(self) -> None:
        # A stale timer from an earlier disconnect must not fire during a later
        # one and mark the coordinator disconnected before that cycle's own
        # grace period elapsed.
        if self._reconnect_timer is not None:
            self._reconnect_timer.cancel()
            self._reconnect_timer = None

    def _connection_reconnect_callback(self) -> None:
        self._reconnect_timer = None
        if not self.appliance.session.connected:
            self.connected = False
            self.async_set_updated_data(None)
