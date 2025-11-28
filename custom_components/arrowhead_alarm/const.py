DOMAIN = "arrowhead_alarm"

# Alarm Command Constants. While the panel expects bytes these are all declared as strings.
# Calls to writer are expected to convert method to bytes before send.

# --- 1. Communication Parameters & Constraints ---

# Default baud rate for the serial connection
BAUD_RATE_DEFAULT = 115200

# Data bits and Stop bits
DATA_BITS = 8
STOP_BITS = 1

# Receive buffer size
RX_BUFFER_SIZE = 512

# Reply timing and attempts for Modes 2 and 3
REPLY_TIMEOUT_MS = 500  # Panel waits 500mS for a reply
REPLY_RETRIES_MAX = 3  # Total of 3 attempts before marking interface down


# --- 2. Mode-Specific Parameters & Delimiters ---

# Default communication mode
MODE_DEFAULT = 1

# Line endings for Mode 1
MODE_1_DELIMITER = ["\r\n", "\n\r"]

# Line ending for Mode 2 and Mode 3
MODE_2_3_DELIMITER = "\n"

# Panel-to-Remote acknowledgment response for command success (e.g., 'OK Version...')
MSG_ACK_OK_TEXT = "OK"

# Remote-to-Panel acknowledgment for status messages (Modes 2, 3)
ACK_SUCCESS_RESPONSE = "OK"


# --- 3. Parameter Limits (Max Numbers) ---

# Maximum number for Zones (used in BYPASS/UNBYPASS)
MAX_ZONES = 64

# Maximum number for Partitions/Areas (used in ARMAWAY/DISARM Mode 2)
MAX_PARTITIONS_AREAS = 32

# Maximum user number (used in ARMAWAY/DISARM Modes 1, 3)
MAX_USER_NUMBER = 2000

# Maximum virtual keypad device number
MAX_VIRTUAL_KEYPAD_DEVICE = 32

# Maximum number of outputs
MAX_OUTPUTS = 32


# --- 4. Remote-to-Panel Command Strings ---

CMD_VERSION = "VERSION"  # Query system version
CMD_DEVICE_QUERY = "DEVICE?"  # Query virtual keypad device #
CMD_DEVICE_SET = "DEVICE"  # Set virtual keypad device #
CMD_ARMAWAY = "ARMAWAY"  # Arm in away mode
CMD_ARMSTAY = "ARMSTAY"  # Arm in stay mode
CMD_DISARM = "DISARM"  # Disarm
CMD_BYPASS = "BYPASS"  # Bypass zone #
CMD_UNBYPASS = "UNBYPASS"  # Clear bypass zone #
CMD_OUTPUT_ON = "OUTPUTON"  # Turn on output #
CMD_OUTPUT_OFF = "OUTPUTOFF"  # Turn off output #
CMD_OUTPUT_QUERY = "OUTPUT"  # Query state of output #
CMD_MEMORY_QUERY = "MEM"  # Query the panel memory
CMD_STATUS = "STATUS"  # Query system status
CMD_MODE = "MODE"  # Set handshake and message mode


# --- 5. Panel-to-Remote Status Messages (Prefixes) ---

# Partition Status Messages
MSG_ARM_AWAY = "A"
MSG_ARM_STAY = "S"
MSG_DISARM = "D"
MSG_PARTITION_ALARM = "AA"  # (Mode 2 only)
MSG_PARTITION_ALARM_RESTORE = "AR"  # (Mode 2 only)
MSG_PARTITION_READY = "RO"
MSG_PARTITION_NOT_READY = "NR"

# Zone Status Messages
MSG_ZONE_OPEN = "ZO"
MSG_ZONE_CLOSED = "ZC"
MSG_ZONE_ALARM = "ZA"
MSG_ZONE_ENTRY = "ZE"
MSG_ZONE_ENTRY_DELAY = "ZEDS"
MSG_ZONE_ALARM_RESTORE = "ZR"
MSG_ZONE_BYPASS = "ZBY"
MSG_ZONE_UNBYPASS_RESTORE = "ZBYR"
MSG_ZONE_TROUBLE_ALARM = "ZT"

# System Status Messages
MSG_SYSTEM_MAINS_FAIL = "MF"
MSG_SYSTEM_MAINS_RESTORE = "MR"
MSG_SYSTEM_BATTERY_LOW = "BF"
MSG_SYSTEM_BATTERY_RESTORE = "BR"


# --- 6. Panel Error Codes (ERR x) ---

ERR_COMMAND_NOT_UNDERSTOOD = "ERR 1"
ERR_INVALID_PARAMETER = "ERR 2"
ERR_NOT_ALLOWED = "ERR 3"
ERR_RX_BUFFER_OVERFLOW = "ERR 4"
ERR_TX_BUFFER_OVERFLOW = "ERR 5"
ERR_XMODEM_FAILED = "ERR 6"
