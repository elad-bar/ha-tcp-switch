from datetime import timedelta

VERSION = '1.0.1'

BUFFER = 1024
SCAN_INTERVAL = timedelta(seconds=60)
DEFAULT_PORT = 6722
DEFAULT_CHANNELS = 2

DEFAULT_MOMENTARY_DELAY = 0

STATUS_COMMAND = '00'

CONF_CHANNELS = 'channels'
CONF_MOMENTARY_DELAY = 'momentary_delay'