"""Handles communication between the Alarm Panel and Home Assistant."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import logging
import re
from typing import Any
import contextlib

MODES = (1, 2, 3)
DELIMITERS = ("\n", "\n\r", "\r\n", "\r")
CMD_MODE = "MODE"
CMD_ARMAWAY = "ARMAWAY"
CMD_ARMSTAY = "ARMSTAY"
CMD_DISARM = "DISARM"
CMD_STATUS = "STATUS"
CMD_BYPASS = "BYPASS"
CMD_UNBYPASS = "UNBYPASS"
CMD_TRIGGER_OUTPUT = "OUTPUTON"


# Map of message prefixes to their corresponding status type and state.
# 'action' helps classify if the status is an activation (True) or a restoration/reset (False).
# Note: ZCx (Closed) is a restoration of ZOx (Open). ZRx (Restored) is a restoration of ZAx (Alarm).
ZONE_STATUS_MAP = {
    # Active/Alarm States (Set to True)
    "ZA": {"status_type": "alarm", "action": True, "description": "Zone is in alarm"},
    "ZBL": {
        "status_type": "battery_low",
        "action": True,
        "description": "Radio zone battery is low",
    },
    "ZBY": {
        "status_type": "bypassed",
        "action": True,
        "description": "Zone is bypassed",
    },
    "ZIA": {
        "status_type": "sensor_watch_alarm",
        "action": True,
        "description": "Sensor watch alarm active",
    },
    "ZO": {
        "status_type": "open",
        "action": True,
        "description": "Zone is open (un-sealed)",
    },
    "ZT": {
        "status_type": "trouble",
        "action": True,
        "description": "Trouble alarm active",
    },
    "ZSA": {
        "status_type": "supervise_alarm",
        "action": True,
        "description": "Supervise alarm active",
    },
    # Restored/Cleared States (Set to False)
    "ZBR": {
        "status_type": "battery_low",
        "action": False,
        "description": "Radio zone battery restored",
    },
    "ZBYR": {
        "status_type": "bypassed",
        "action": False,
        "description": "Zone bypass removed (un-bypassed)",
    },
    "ZC": {
        "status_type": "open",
        "action": False,
        "description": "Zone is closed (sealed)",
    },
    "ZIR": {
        "status_type": "sensor_watch_alarm",
        "action": False,
        "description": "Sensor watch alarm restored",
    },
    "ZR": {
        "status_type": "alarm",
        "action": False,
        "description": "Zone alarm restored",
    },
    "ZTR": {
        "status_type": "trouble",
        "action": False,
        "description": "Trouble alarm restored",
    },
    "ZSR": {
        "status_type": "supervise_alarm",
        "action": False,
        "description": "Supervise alarm restored",
    },
}

PARTITION_STATUS_MAP = {
    # PARTITION Status Messages (Requires Partition number x)
    "A": "partition_away_armed",  # Partition x has away-armed
    "AA": "partition_in_alarm",  # Partition x is in alarm
    "AR": "partition_alarm_restored",  # Partition x is no longer in alarm
    "D": "partition_disarmed",  # Partition x has disarmed
    "EA": "partition_exit_away_timing",  # Partition x started away-arm exit period
    "ES": "partition_exit_stay_timing",  # Partition x started stay-arm exit period
    "NR": "partition_not_ready",  # Partition x is not ready (not sealed)
    "RO": "partition_ready",  # Partition x is ready (sealed)
    "S": "partition_stay_armed",  # Partition x has stay-armed
    "OO": "output_on",
    "OR": "output_ready",
}

# Regex pattern to capture the prefix (2-4 characters) and the zone number (1-2 digits)
# Example matches: 'ZA12', 'ZBYR1', 'ZO5'
PARTITION_MESSAGE_PATTERN = re.compile(r"^([A-Z]{1,2})(\d{1,2})$")
ZONE_MESSAGE_PATTERN = re.compile(r"^(Z[A-Z]{1,3})(\d{1,2})$")

_LOGGER = logging.getLogger(__name__)


class ArrowheadAlarmAPI:
    """Handles communication to the Arrowhead Alarm Panel."""

    def __init__(self, host: str, port: int) -> None:
        """Initialies the Arrowhead Alarm API.

        Parameter:
            host: the ip address of the panel / serial device server.
            port: the port for the panel / serial device server.
        """

        self.host = host
        self.port = port

        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None

        self._queue: asyncio.Queue[str] = asyncio.Queue()

        self._listen_task: asyncio.Task | None = None
        self._consumer_task: asyncio.Task | None = None

        self._callbacks: list[Callable[[dict[str, Any]], Awaitable[None]]] = []

    def register_callback(
        self, cb: Callable[[dict[str, Any]], Awaitable[None]]
    ) -> None:
        """Registers a callback for incoming panel messages."""
        self._callbacks.append(cb)

    @property
    def is_connected(self) -> bool:
        """Returns True if the Connection is active."""

        return self.writer is not None and not self.writer.is_closing()

    async def set_user(self, pin: int, user: int) -> None:
        """Sets the user for the connection and pin.

        Parameter: user - allowed values 1 - 100
        """
        if user not in range(1, 100):
            raise ValueError("User must be between 1 and 100.")
        cmd = f"P1E{user}={pin}"

        await self._send_command(cmd)

    async def connect(self) -> None:
        """Establishes the connection."""
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

        # Start both tasks
        self._listen_task = asyncio.create_task(self.listen(), name="AAP_Listener")
        self._consumer_task = asyncio.create_task(
            self._message_consumer(), name="AAP_Consumer"
        )

    async def set_mode(self, mode: int = 2) -> None:
        """Sets the mode for the connection.

        Parameter: mode - allowed values 1,2,3

        Return:
            True if successful - i.e. return is MODE 2
            False if not
        """

        if mode not in MODES:
            raise ValueError("Mode must be 1, 2, or 3.")

        # Our standard operating mode will be mode 2, which users \n for delimiter.
        # For now we need to assume that we are in mode 1 and use a newline that works for both MODE 2 and MODE 1
        cmd = f"{CMD_MODE} {mode}"

        await self._send_command(cmd, 2)

    async def arm_away(self, area: int = 1) -> None:
        """Arms the system in away mode.

        Parameters:
            area - the area to be armed.
        """

        cmd = f"{CMD_ARMAWAY} {area}"

        await self._send_command(cmd)

    async def arm_stay(self, area: int = 1) -> None:
        """Arms the system in stay mode.

        Parameters:
            area - the area to be armed.
        """

        cmd = f"{CMD_ARMSTAY} {area}"

        await self._send_command(cmd)

    async def disarm(self, pin: int, area: int = 1) -> None:
        """Disarms the system.

        Parameters:
            pin - the pin to disarm the system.
            area - the area to be disarmed.
        """

        cmd = f"{CMD_DISARM} {area} {pin}"

        await self._send_command(cmd)

    async def bypass_zone(self, zone: int) -> None:
        """Bypasses a zone.

        Parameters:
            zone - the zone to be bypassed.
        """
        cmd = f"{CMD_BYPASS} {zone}"
        await self._send_command(cmd)

    async def unbypass_zone(self, zone: int) -> None:
        """Unbypasses a zone.

        Parameters:
            zone - the zone to be unbypassed.
        """
        cmd = f"{CMD_UNBYPASS} {zone}"
        await self._send_command(cmd)

    async def trigger_output(self, output: int) -> None:
        """Triggers an output.

        Parameters:
            output - the output to be triggered.
        """
        _LOGGER.info("Triggered Output: %s", output)
        cmd = f"{CMD_TRIGGER_OUTPUT} {output}"
        await self._send_command(cmd)

    async def request_status(self) -> None:
        """Requests the status of the system."""
        cmd = CMD_STATUS
        await self._send_command(cmd)

    async def listen(self) -> None:
        """Listens for incoming messages from the Alarm Panel."""
        if not self.reader:
            raise ConnectionError("Not connected to the Alarm Panel.")

        buffer = b""
        try:
            while True:
                data = await self.reader.read(512)
                if not data:
                    break
                buffer += data
                buffer = self._normalize_delimiter(buffer)

                while DELIMITERS[0].encode("ascii") in buffer:
                    # Extract complete message
                    line, buffer = buffer.split(DELIMITERS[0].encode("ascii"), 1)
                    message = line.decode("ascii", errors="replace")

                    # Acknowledge receipt
                    await self._ack()

                    self._queue.put_nowait(message)

        except asyncio.CancelledError:
            _LOGGER.debug("Listening task cancelled")
            raise
        except Exception as e:
            _LOGGER.exception("Error while listening: %s", e)
            raise

    async def _message_consumer(self) -> None:
        """Background task to process the queue without blocking the listener."""

        while True:
            message = await self._queue.get()

            data = self._translate_message(message)

            try:
                # Notify all registered callbacks
                if data:
                    await asyncio.gather(*(cb(data) for cb in self._callbacks))
            except Exception as e:
                # Yes we are catching a generic exception here, but reasons:
                # 1. We don't expect it to fail and this is not production code.
                #       If I notice errors in my HA instance or want to distribute this wide
                #       then I'll do some more work on this.
                # 2. We don't want an error here to cause a silent failure of the message consumer.
                _LOGGER.error("Failed to process message '%s': %s", message, e)

                # We don't know what state we might have missed, so force a resync.
                await self.request_status()
            finally:
                self._queue.task_done()

    async def close_connection(self) -> None:
        """Closes the connection to the Alarm Panel."""

        # Cancel tasks
        for task in [self._listen_task, self._consumer_task]:
            if task and not task.done():
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

        self._listen_task = None
        self._consumer_task = None
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()

    async def _send_command(self, command: str, delimiter_index: int = 0) -> None:
        r"""Sends a command to the Alarm Panel.

        Parameter: command - the command to send
                   delimiter_index - delimiter index to use (default 0 = \n), options 0, 1, 2
        """
        if not self.writer:
            raise ConnectionError("Not connected to the Alarm Panel.")
        if delimiter_index not in [0, 1, 2]:
            raise ValueError("Delimiter index must be 0, 1, or 2.")

        cmd = f"{command}{DELIMITERS[delimiter_index]}"
        b_cmd = cmd.encode("ascii")
        self.writer.write(b_cmd)
        await self.writer.drain()

    async def _ack(self) -> None:
        """Sends an acknowledgment to the Alarm Panel."""
        if self.writer:
            self.writer.write(b"OK\n")
            await self.writer.drain()

    def _normalize_delimiter(self, data: bytes) -> bytes:
        r"""Normalizes delimiters in the incoming data to use only \n."""
        for delim in DELIMITERS[1:]:
            data = data.replace(delim.encode("ascii"), DELIMITERS[0].encode("ascii"))
        return data

    def _translate_message(self, message: str) -> dict[str, Any]:
        """Translates a raw message into a structured dict, included a type key."""

        raw_message = message.strip().upper()

        if "OK STATUS" in raw_message:
            return {"type": "sync_start"}

        if "OK OUTPUTON" in raw_message:
            return {
                "type": "command_response",
                "data": {"status": "success", "command": "output"},
            }

        # Handle ERR Responses (e.g., ERR 1, ERR 05)
        if raw_message.startswith("ERR"):
            try:
                err_code = int(raw_message.split()[1])
                return {  # noqa: TRY300
                    "type": "command_response",
                    "data": {"status": "error", "code": err_code},
                }
            except (IndexError, ValueError):
                return {
                    "type": "command_response",
                    "data": {"status": "error", "code": 0},
                }

        zone_match = ZONE_MESSAGE_PATTERN.match(raw_message)

        # Check if it's a zone first
        if zone_match:
            prefix, zone_id = zone_match.groups()
            status_info = ZONE_STATUS_MAP.get(prefix)
            if status_info:
                zone_id = int(zone_id)
                return {
                    "type": "zone",
                    "data": {
                        "zone_id": zone_id,
                        "status_type": status_info["status_type"],
                        "action": status_info["action"],
                    },
                }

        partition_match = PARTITION_MESSAGE_PATTERN.match(raw_message)

        if partition_match:
            prefix, area_id = partition_match.groups()
            status_string = PARTITION_STATUS_MAP.get(prefix)
            return {
                "type": "partition",
                "data": {
                    "area_id": int(area_id),
                    "status": status_string,
                    "raw_code": prefix,
                },
            }

        return {}
