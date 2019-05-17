"""
Support for TCP Switch.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.vera/
"""
import logging
import socket

from time import sleep
from homeassistant.const import (CONF_NAME, CONF_HOST, CONF_PORT)

from .const import *

_LOGGER = logging.getLogger(__name__)


class TcpSwitchConnection:
    def __init__(self, config):
        try:
            self._switch_name = config.get(CONF_NAME)
            self._channels = config.get(CONF_CHANNELS)

            self._hostname = config.get(CONF_HOST)
            self._port = config.get(CONF_PORT)
            self._momentary_delay = config.get(CONF_MOMENTARY_DELAY)

            self._details = f"TCP Switch {self._hostname}:{self._port}"

            self._skt = None
            self._connected = False

            _LOGGER.info(f'Initializing {self._switch_name} - {self._details} with {self._channels} channels')

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

        except Exception as ex:
            _LOGGER.error(f'Errors while loading configuration due to exception: {str(ex)}')

    @property
    def channels(self):
        return self._channels

    @property
    def switch_name(self):
        return self._switch_name

    def connect(self):
        try:
            _LOGGER.debug(f"Connecting to {self._details}")

            self._skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._skt.connect((self._hostname, self._port))
            self._connected = True

            _LOGGER.debug(f"Connection to {self._details} available")

        except Exception as ex:
            _LOGGER.error(f"Failed to connect to {self._details}, Error: {str(ex)}")
            self.disconnect()

    def disconnect(self):
        try:
            if self._skt is not None:
                _LOGGER.debug(f"Terminating connection from {self._details}")

                self._skt.close()

                _LOGGER.debug(f"Connection from {self._details} terminated")
        except Exception as ex:
            _LOGGER.error(f"Failed to disconnect from {self._details}, Error: {str(ex)}")

        finally:
            self._connected = False
            self._skt = None

    def turn_on(self, channel):
        result = self._toggle(channel, TURN_ON)

        return result

    def turn_off(self, channel):
        result = self._toggle(channel, TURN_OFF)

        return result

    def _toggle(self, channel, action):
        message = f"{action}{channel}"
        duration = ""

        if self._momentary_delay > 0:
            duration = f"({self._momentary_delay} seconds)"
            message = f"{message}:{self._momentary_delay}"

        _LOGGER.info(f"CH#{channel} - {ACTION_DESCRIPTION[action]}{duration} @{self._details}")

        result = self._send_message(f"{message}")

        sleep(self._momentary_delay)

        return result

    def get_status(self, channel):
        status = False
        result = self._send_message(STATUS_COMMAND)

        if result is not None:
            value = result.decode(ENCODING)
            channel_status = value[channel]

            status = channel_status == str(TURN_ON)

        return status

    def get_status_description(self, channel):
        status = self.get_status(channel)

        result = f"Channel #{channel}: {status}"

        return result

    def _send_message(self, message, retry=0):

        if retry == 0:
            _LOGGER.debug(f"Starting to send message: {message}")
        else:
            _LOGGER.debug(f"Resending message (#{retry}): {message}")

        if not self._connected:
            self.connect()

        self._skt.send(message.encode(ENCODING))
        result = self._skt.recv(1024)

        if result is None or result == '':
            _LOGGER.debug(f"Invalid response from {self._details}")
            self.disconnect()

            retry = retry + 1

            if retry <= MAX_RETRIES:
                result = self._send_message(message, retry)

        return result
