"""
Support for TCP Switch.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.vera/
"""
import logging
import socket

import voluptuous as vol
from homeassistant.components.switch import SwitchDevice, DOMAIN
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv

from homeassistant.const import (CONF_NAME, CONF_HOST, CONF_PORT,
                                 EVENT_HOMEASSISTANT_START,
                                 EVENT_HOMEASSISTANT_STOP)
from homeassistant.helpers.event import track_time_interval

from .const import *

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONF_CHANNELS, default=DEFAULT_CHANNELS): cv.byte,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    vol.Optional(CONF_MOMENTARY_DELAY, default=DEFAULT_MOMENTARY_DELAY): cv.byte
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the TCP switches."""
    scan_interval = SCAN_INTERVAL

    try:
        switch_name = config.get(CONF_NAME)
        server_name = config.get(CONF_HOST)
        server_port = config.get(CONF_PORT)
        momentary_delay = config.get(CONF_MOMENTARY_DELAY)
        channels = config.get(CONF_CHANNELS)
        scan_interval_seconds = scan_interval.total_seconds()

        if 0 < momentary_delay < scan_interval_seconds:
            scan_interval = timedelta(seconds=momentary_delay)

        _LOGGER.info(f'Starting to initialize {switch_name} - {server_name}:{server_port} with {channels} channels')

        devices = []
        for channel in range(channels):
            device = TcpSwitch(switch_name, server_name, server_port, channel + 1, momentary_delay)
            devices.append(device)

        add_entities(devices, True)

        def tcp_switch_refresh(event_time):
            """Call TCP Switch to refresh information."""
            _LOGGER.debug(f'Updating TCP Switch, at {event_time}')
            for device_item in devices:
                device_item.update()

        def tcp_switch_connect(event_time):
            """Call TCP Switch to connect and update."""
            _LOGGER.debug(f'Connecting and updating TCP Switch, at {event_time}')
            for device_item in devices:
                device_item.update()

        def tcp_switch_disconnect(event_time):
            """Call TCP Switch to disconnect."""
            _LOGGER.debug(f'Disconnecting TCP Switch, at {event_time}')
            for device_item in devices:
                device_item.disconnect()

        # register service
        hass.services.register(DOMAIN, 'connect', tcp_switch_connect)
        hass.services.register(DOMAIN, 'disconnect', tcp_switch_disconnect)

        hass.bus.listen_once(EVENT_HOMEASSISTANT_START, tcp_switch_connect)
        hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, tcp_switch_disconnect)

        # register scan interval for Home Automation Manager (HAM)
        track_time_interval(hass, tcp_switch_refresh, scan_interval)

        return True

    except Exception as ex:
        _LOGGER.error(f'Errors while loading configuration due to exception: {str(ex)}')

        return False


class TcpSwitch(SwitchDevice):
    """Representation of a Vera Switch."""

    def __init__(self, switch_name, server_name, server_port, channel, momentary_delay):
        """Initialize the Vera device."""
        self._state = False
        self._channel = channel
        self._server_name = server_name
        self._server_port = server_port
        self._switch_name = switch_name
        self._momentary_delay = momentary_delay
        self._socket = None
        self._connected = False

        self._host_details = f'{NAME} {self._server_name}:{self._server_port} CH#{self._channel}'

    def connect(self):
        try:
            _LOGGER.debug("Connecting")
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((self._server_name, self._server_port))
            self._connected = True

        except Exception as ex:
            host = f'{self._server_name}:{self._server_port}'
            error_message = f'Failed to connect {self._host_details}, Error: {str(ex)}'

            _LOGGER.error(error_message)
            self._connected = False

        _LOGGER.debug("Connected")

    def disconnect(self):
        try:
            _LOGGER.debug("Disconnecting")
            self._socket.close()

        except Exception as ex:
            host = f'{self._server_name}:{self._server_port}'
            error_message = f'Failed to disconnect {self._host_details}, Error: {str(ex)}'
            _LOGGER.error(error_message)

        finally:
            self._socket = None
            self._connected = False
            _LOGGER.debug("Disconnected")

    def turn_on(self, **kwargs):
        """Turn device on."""
        self.toggle(True)

        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Turn device off."""
        self.toggle(False)

        self.schedule_update_ha_state()

    @property
    def is_connected(self):
        """Return the name of this camera."""
        return self._connected

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
        self._state = self.send_tcp_message(STATUS_COMMAND)

    def send_tcp_message(self, message):
        result = None
        try:
            error_message = f'Cannot send {self._host_details} message: {message}'

            if not self.is_connected:
                self.connect()

            if self.is_connected:
                _LOGGER.debug(f'Sending {message}')

                self._socket.send(message.encode('utf-8'))

                _LOGGER.debug("Getting data")

                data = str(self._socket.recv(BUFFER))

                channel_id = self._channel - 1

                _LOGGER.debug(f'Parsing {data}')

                status = data[channel_id]

                result = status == "1"
            else:
                _LOGGER.error(f'{error_message}')

        except Exception as ex:
            _LOGGER.error(f'{error_message}, Error: {str(ex)}')

        return result

    def toggle(self, turn_on):
        cmd = '2'
        delay = ""

        if turn_on:
            cmd = '1'

        if self._momentary_delay > 0:
            delay = f':{self._momentary_delay}'

        data = f'{cmd}{str(self._channel)}{delay}'

        self._state = self.send_tcp_message(data)
