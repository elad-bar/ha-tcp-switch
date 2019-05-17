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
            self._channels = config.get(CONF_CHANNELS, [])

            self._hostname = config.get(CONF_HOST)
            self._port = config.get(CONF_PORT)
            self._momentary_delay = config.get(CONF_MOMENTARY_DELAY)

            self._details = f"{NAME} {self._hostname}:{self._port}"

            self._skt = None
            self._connected = False

            _LOGGER.info(f'Initializing {self._switch_name} - {self._details} with {self._channels} channels')

            def tcp_switch_connect(event_time):
                """Call TCP Switch to connect and update."""
                _LOGGER.debug(f'Connecting and updating {NAME}, at {event_time}')
                self._connect()

            def tcp_switch_disconnect(event_time):
                """Call TCP Switch to disconnect."""
                _LOGGER.debug(f'Disconnecting {NAME}, at {event_time}')
                self._disconnect()

            self.connect = tcp_switch_connect
            self.disconnect = tcp_switch_disconnect

        except Exception as ex:
            _LOGGER.error(f'Errors while loading configuration due to exception: {str(ex)}')

    @property
    def channels(self):
        return self._channels

    @property
    def switch_name(self):
        return self._switch_name

    def _connect(self):
        try:
            _LOGGER.debug(f"Connecting to {self._details}")

            self._disconnect()

            self._skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._skt.connect((self._hostname, self._port))
            self._connected = True

            _LOGGER.debug(f"Connection to {self._details} available")

        except Exception as ex:
            _LOGGER.error(f"Failed to connect to {self._details}, Error: {str(ex)}")
            self._disconnect()

    def _disconnect(self):
        try:
            if self._skt:
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

        if self._momentary_delay > 0:
            message = f"{message}:{self._momentary_delay}"

        _LOGGER.info(f"{self._details} CH#{channel} - {ACTION_DESCRIPTION[action]}")

        result = self._send_message(message)

        sleep(self._momentary_delay)

        return result

    def get_status(self, channel):
        status = False
        result = self._send_message(STATUS_COMMAND)

        if result:
            channel_status = result[channel]

            status = channel_status == str(TURN_ON)

        return status

    def _send_message(self, message, retry=0):
        result = None

        if retry == 0:
            _LOGGER.debug(f"Starting to send message: {message}")
        else:
            _LOGGER.debug(f"Resending message (#{retry}): {message}")

        if not self._connected:
            self._connect()

        try:
            self._skt.send(message.encode(ENCODING))
            result_data = self._skt.recv(BUFFER)

            if result_data is not None:
                result = result_data.decode(ENCODING)

            _LOGGER.debug(f"Response of message {message} (#{retry}): {result}")

        except Exception as ex:
            _LOGGER.warning(f"Failed to extract result for message: {message}, Error: {str(ex)}")

        if not result:
            _LOGGER.debug(f"Invalid response from {self._details}")

            retry = retry + 1

            if retry <= MAX_RETRIES:
                result = self._send_message(message, retry)
            else:
                result = None

                _LOGGER.error(f"Maximum retries exceeded for message: {message}")

        return result
