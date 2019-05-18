"""
Support for TCP Switch.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.vera/
"""
import logging

import voluptuous as vol
from homeassistant.components.switch import SwitchDevice
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv

from homeassistant.const import (CONF_NAME, CONF_HOST, CONF_PORT,
                                 EVENT_HOMEASSISTANT_START)
from homeassistant.helpers.event import track_time_interval

from .const import *
from .connection import TcpSwitchConnection

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONF_CHANNELS, default=[]):
        vol.All(cv.ensure_list, [cv.byte]),
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    vol.Optional(CONF_MOMENTARY_DELAY, default=DEFAULT_MOMENTARY_DELAY): cv.byte
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the TCP switches."""
    is_initialized = False

    try:
        _LOGGER.info(f'Loading configuration of {NAME}, DI: {discovery_info}')

        manager = TcpSwitchConnection(config)

        def ts_update(event_time):
            _LOGGER.debug(f"Updating {NAME} ({event_time})")
            for switch in devices:
                switch.update()

        if manager.channels:
            devices = []
            for channel in manager.channels:
                device = TcpSwitch(manager, channel)
                devices.append(device)

            hass.bus.listen_once(EVENT_HOMEASSISTANT_START, ts_update)

            # register scan interval for Home Automation Manager (HAM)
            track_time_interval(hass, ts_update, SCAN_INTERVAL)

            add_entities(devices, True)

            is_initialized = True

    except Exception as ex:
        _LOGGER.error(f'Errors while loading configuration due to exception: {str(ex)}')

    return is_initialized


class TcpSwitch(SwitchDevice):
    """Representation of a Vera Switch."""

    def __init__(self, connection, channel):
        """Initialize the Vera device."""
        self._channel = channel
        self._connection = connection
        self._switch_name = self._connection.switch_name
        self._state = False

    def turn_on(self, **kwargs):
        """Turn device on."""
        self._connection.turn_on(self._channel)

        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Turn device off."""
        self._connection.turn_off(self._channel)

        self.schedule_update_ha_state()

    @property
    def name(self):
        """Return the name of this camera."""
        return f'{self._switch_name} CH{self._channel}'

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    def update(self):
        """Update device state."""
        self._state = self._connection.get_status(self._channel)
