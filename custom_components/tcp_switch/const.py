from datetime import timedelta

VERSION = '1.0.7'

BUFFER = 1024
SCAN_INTERVAL = timedelta(seconds=60)
DEFAULT_PORT = 6722
DEFAULT_CHANNELS = 2

DEFAULT_MOMENTARY_DELAY = 0

STATUS_COMMAND = '00'

CONF_CHANNELS = 'channels'
CONF_MOMENTARY_DELAY = 'momentary_delay'
NAME = "TCP Switch"


TURN_ON = 1
TURN_OFF = 2

ACTION_DESCRIPTION = {
    TURN_ON: "Turn On",
    TURN_OFF: "Turn Off",
}

ENCODING = 'utf-8'
MAX_RETRIES = 3
