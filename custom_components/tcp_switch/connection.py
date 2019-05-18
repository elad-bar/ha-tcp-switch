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

            _LOGGER.info(f'Initializing {self._switch_name} - {self._details} with {self._channels} channels')

        except Exception as ex:
            _LOGGER.error(f'Errors while loading configuration due to exception: {str(ex)}')

    @property
    def channels(self):
        return self._channels

    @property
    def switch_name(self):
        return self._switch_name

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
        failure_reason = None

        if retry == 0:
            _LOGGER.debug(f"Starting to send message: {message}")
        else:
            _LOGGER.debug(f"Resending message (#{retry}): {message}")

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as skt:
                skt.connect((self._hostname, self._port))
                skt.send(message.encode(ENCODING))
                result_data = skt.recv(BUFFER)

                if result_data is not None:
                    result = result_data.decode(ENCODING)

            _LOGGER.debug(f"Response of message {message} (#{retry}): {result}")

        except Exception as ex:
            failure_reason = str(ex)

        if not result:
            _LOGGER.debug(f"Invalid response from {self._details}")

            retry = retry + 1

            if retry <= MAX_RETRIES:
                result = self._send_message(message, retry)
            else:
                result = None

                if failure_reason:
                    failure_reason = f", Error: {failure_reason}"

                _LOGGER.error(f"Maximum retries exceeded for message: {message}{failure_reason}")

        return result
