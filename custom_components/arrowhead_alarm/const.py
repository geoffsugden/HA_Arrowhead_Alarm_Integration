"""Contains constants specific to the arrowhead alarm integration."""

DOMAIN = "arrowhead_alarm"
DEFAULT_SCAN_INTERVAL = 60

CONTROLS = "controls"
CONTROL_COUNT = "control_count"
CONTROL_NUMBER = "control_number"
CONTROL_NAME = "control_name"

# Configuration Keys
ZONES = "zones"
ZONE_COUNT = "zone_count"
ZONE_NUMBER = "zone_number"
ZONE_NAME = "zone_name"
ZONE_TYPE = "zone_type"

ZONE_TYPES = ["motion", "garage_door", "door"]


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


ALARM_ALL_STATUS_MESSAGES = {
    # -----------------------------------------------------------------
    # SYSTEM Status Messages (No parameters: BF, BR, CAL, CLF, etc.)
    "BF": "system_battery_low",  # System battery low/missing
    "BR": "system_battery_restored",  # System battery restored
    "CAL": "comms_to_station_started",  # Communication to monitoring station started
    "CLF": "comms_to_station_finished",  # Communication to monitoring station finished
    "DF": "dialer_failed",  # Dialer (comms) failed
    "DR": "dialer_restored",  # Dialer (comms) restored
    "FF": "system_fuse_fault",  # System fuse fault
    "FR": "system_fuse_restored",  # System fuse restore
    "LF": "dialer_line_fault",  # Dialer (comms) line fault
    "LR": "dialer_line_restored",  # Dialer (comms) line restored
    "MF": "mains_power_failure",  # Mains power failure
    "MR": "mains_power_restore",  # Mains power restore
    "RIF": "receiver_fault",  # Receiver fault
    "RIR": "receiver_restored",  # Receiver restore
    # SYSTEM Status Messages (With parameter: Pendant x)
    "PBF": "pendant_battery_low",  # Pendant x battery low
    "PBR": "pendant_battery_restored",  # Pendant x battery restored
    # -----------------------------------------------------------------
    # PARTITION Status Messages (Requires Partition number x)
    "A": "partition_away_armed",  # Partition x has away-armed
    "AA": "partition_in_alarm",  # Partition x is in alarm (Note: AA is overloaded for Output x off)
    "AR": "partition_alarm_restored",  # Partition x is no longer in alarm
    "D": "partition_disarmed",  # Partition x has disarmed
    "EA": "partition_exit_away_timing",  # Partition x started away-arm exit period
    "ES": "partition_exit_stay_timing",  # Partition x started stay-arm exit period
    "NR": "partition_not_ready",  # Partition x is not ready (not sealed)
    "RO": "partition_ready",  # Partition x is ready (sealed)
    "S": "partition_stay_armed",  # Partition x has stay-armed
    # -----------------------------------------------------------------
    # ZONE Status Messages (Requires Zone number x)
    "ZA": "zone_alarm",  # Zone x is in alarm
    "ZBL": "zone_battery_low",  # Radio zone x battery low
    "ZBR": "zone_battery_restored",  # Radio zone x battery restored
    "ZBY": "zone_bypassed",  # Zone x bypassed
    "ZBYR": "zone_unbypassed",  # Zone x unbypassed
    "ZC": "zone_closed",  # Zone x closed (sealed)
    "ZIA": "zone_sensor_watch_alarm",  # Zone x sensor-watch alarm
    "ZIR": "zone_sensor_watch_restored",  # Zone x sensor-watch restored
    "ZO": "zone_open",  # Zone x open (un-sealed)
    "ZR": "zone_alarm_restored",  # Zone x alarm restored
    "ZT": "zone_trouble_alarm",  # Zone x trouble alarm
    "ZTR": "zone_trouble_restored",  # Zone x trouble alarm restored
    "ZSA": "zone_supervise_alarm",  # Zone x supervise alarm
    "ZSR": "zone_supervise_restored",  # Zone x supervise alarm restored
    # -----------------------------------------------------------------
    # OUTPUT Status Messages (Requires Output number x)
    "OO": "output_on",  # Output x on
    "OR": "output_off",  # Output x off
}


# --- 6. Panel Error Codes (ERR x) ---

ERR_COMMAND_NOT_UNDERSTOOD = "ERR 1"
ERR_INVALID_PARAMETER = "ERR 2"
ERR_NOT_ALLOWED = "ERR 3"
ERR_RX_BUFFER_OVERFLOW = "ERR 4"
ERR_TX_BUFFER_OVERFLOW = "ERR 5"
ERR_XMODEM_FAILED = "ERR 6"
