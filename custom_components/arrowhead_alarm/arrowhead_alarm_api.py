"""Handles communication between the Alarm Panel and Home Assistant."""

from __future__ import annotations
import asyncio
from typing import Callable, Awaitable

import logging

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

_LOGGER = logging.getLogger(__name__)


class ArrowheadAlarmAPI:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None

        self._callbacks: list[Callable[[str], Awaitable[None]]] = []

    def register_callback(self, cb: Callable[[str], Awaitable[None]]) -> None:
        """Registers a callback for incoming panel messages."""
        self._callbacks.append(cb)

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

                    # Notify all registered callbacks
                    await asyncio.gather(*(cb(message) for cb in self._callbacks))

        except asyncio.CancelledError:
            _LOGGER.debug("Listening task cancelled.")
            raise
        except Exception as e:
            _LOGGER.exception(f"Error while listening: {e}")
            raise

    async def close_connection(self) -> None:
        """Closes the connection to the Alarm Panel."""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()

    async def _send_command(self, command: str, delimiter_index: int = 0) -> None:
        """Sends a command to the Alarm Panel.

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
        """Normalizes delimiters in the incoming data to use only \n."""
        for delim in DELIMITERS[1:]:
            data = data.replace(delim.encode("ascii"), DELIMITERS[0].encode("ascii"))
        return data
