"""
Support for TCP Switch.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.vera/
"""
import logging
import socket

from homeassistant.const import (CONF_NAME, CONF_HOST, CONF_PORT)

from .const import *

_LOGGER = logging.getLogger(__name__)


class TcpSwitchConnection:
    def __init__(self, config):
        self._scan_interval = SCAN_INTERVAL

        try:
            self._switch_name = config.get(CONF_NAME)
            self._server_name = config.get(CONF_HOST)
            self._server_port = config.get(CONF_PORT)
            self._momentary_delay = config.get(CONF_MOMENTARY_DELAY)
            self._channels = config.get(CONF_CHANNELS)
            self._scan_interval_seconds = self._scan_interval.total_seconds()
            self._data = None

            self._socket = None
            self._connected = False
            self._connecting = False

            self._host_details = f'TCP Switch {self._server_name}:{self._server_port}'

            if 0 < self._momentary_delay < self._scan_interval_seconds:
                self._scan_interval = timedelta(seconds=self._momentary_delay)

            _LOGGER.info(f'Initializing {self._switch_name} - {self._host_details} with {self._channels} channels')

            def tcp_switch_refresh(event_time):
                """Call TCP Switch to refresh information."""
                _LOGGER.debug(f'Updating TCP Switch, at {event_time}')
                self.update_status()

            def tcp_switch_connect(event_time):
                """Call TCP Switch to connect and update."""
                _LOGGER.debug(f'Connecting and updating TCP Switch, at {event_time}')
                self.connect()

            def tcp_switch_disconnect(event_time):
                """Call TCP Switch to disconnect."""
                _LOGGER.debug(f'Disconnecting TCP Switch, at {event_time}')
                self.disconnect()

            self.tcp_switch_connect = tcp_switch_connect
            self.tcp_switch_disconnect = tcp_switch_disconnect
            self.tcp_switch_refresh = tcp_switch_refresh

        except Exception as ex:
            _LOGGER.error(f'Errors while loading configuration due to exception: {str(ex)}')

    @property
    def channels(self):
        return self._channels

    @property
    def switch_name(self):
        return self._switch_name

    @property
    def scan_interval(self):
        return self._scan_interval

    def connect(self):
        try:
            if not self._connected and not self._connecting:
                self._connecting = True

                _LOGGER.info(f"Connecting to {self._host_details}")

                self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._socket.connect((self._server_name, self._server_port))
                self._connected = True

                _LOGGER.info(f"{self._host_details} connected")

        except Exception as ex:
            _LOGGER.error(f'Failed to connect {self._host_details}, Error: {str(ex)}')
            self._connected = False
        finally:
            self._connecting = False

    def disconnect(self):
        try:
            _LOGGER.info(f"Disconnecting from {self._host_details}")
            self._socket.close()

        except Exception as ex:
            _LOGGER.error(f'Failed to disconnect {self._host_details}, Error: {str(ex)}')

        finally:
            self._socket = None
            self._connected = False

            _LOGGER.info(f"{self._host_details} connection terminated")

    def send_tcp_message(self, message):
        error_message = f'Cannot send {self._host_details} message: {message}'

        result = None

        try:

            if not self._connecting:
                if not self._connected:
                    self.connect()

                if self._connected:
                    _LOGGER.debug(f'Sending {message}')

                    self._socket.send(message.encode('utf-8'))

                    _LOGGER.debug("Getting data")

                    result = str(self._socket.recv(BUFFER))
                else:
                    _LOGGER.error(f'{error_message}')

        except Exception as ex:
            _LOGGER.error(f'{error_message}, Error: {str(ex)}')

        return result

    def update_status(self):
        msg = STATUS_COMMAND

        self._data = self.send_tcp_message(msg)

    def toggle(self, turn_on, channel):
        cmd = '2'
        delay = ""

        if turn_on:
            cmd = '1'

        if self._momentary_delay > 0:
            delay = f':{self._momentary_delay}'

        msg = f'{cmd}{str(channel)}{delay}'

        self._data = self.send_tcp_message(msg)

    def get_status(self, channel):
        result = False

        if self._data is not None:
            _LOGGER.debug(f'Parsing {self._data}')

            status = self._data[channel]

            result = status == "1"

        return result
