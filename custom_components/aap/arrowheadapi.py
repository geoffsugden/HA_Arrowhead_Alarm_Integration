"""Handles the back and forth between the alarm panel and home assistant."""

from __future__ import annotations
from typing import Any

import asyncio
import logging

from .const import CMD_MODE, CMD_STATUS, MODE_1_DELIMITER

_LOGGER = logging.getLogger(__name__)


class ArrowheadAPI:
    """Defines methods for communication with Arrowhead Alarm panel."""

    def __init__(self, host: str, port: str) -> None:
        """Create the API task defining the requried parameters."""
        self.host = host
        self.port = port
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None

    @classmethod
    async def create(cls, host: str, port: str) -> ArrowheadAPI:
        """Factory method to create and connect the API instance."""

        instance = cls(host, port)
        instance.reader, instance.writer = await asyncio.open_connection(host, port)
        return instance

    async def validate_set_mode(self, host: str, port: str) -> dict[str, Any]:
        """Confirms connnection available and sets panel to Mode 2.

        Returns:
            bool: True if connection succesful and MODE 2 response recieved. Otherwise False
        """
        # Seconds to wait for validation process.
        timeout = 5.0
        try:
            # Use asyncio.run() to execute the asynchronous core function synchronously
            return await self._async_validate_mode(host, port, timeout)
        except TimeoutError:
            _LOGGER.debug("Validation of AAP Connection failed due to timeout error")
            return {"succes": False, "message": "Failed to connect due to timout Error"}
        except Exception as e:  # noqa: BLE001
            return {
                "succes": False,
                "message": f"Validation of AAP Connection failed due to exception: {e}",
            }

    async def _async_validate_mode(
        self, host: str, port: str, timeout: float = 5, mode: int = 2
    ) -> [str, Any]:  # type: ignore
        """Validates Connection and sets mode. Intended to be called by Static Method only so doens't check for class instance."""

        reader = None
        writer = None

        expected_response = f"MODE {mode}".encode("ascii")

        try:
            # 1. Establish Connection with Timeout
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=timeout
            )

            # 2. Send the command
            mode_command = f"{CMD_MODE} {mode}{MODE_1_DELIMITER[1]}"
            cmd = mode_command.encode("ascii")
            writer.write(cmd)
            await writer.drain()

            # 3. Read the response (or time out). 512 is the maximum byte length returned from the panel.
            buffer = b""
            while True:
                d_chunk = await asyncio.wait_for(reader.read(512), timeout=timeout)

                if not d_chunk:
                    return {
                        "success": False,
                        "message": "Connection closed by panel before mode response recieved",
                    }

                buffer += d_chunk

                if expected_response in buffer:
                    return {"success": True, "message": "Validation succesful"}

                if len(buffer) > 8192:
                    return {
                        "success": False,
                        "message": "Validation buffer exceeded 8kb",
                    }
        finally:
            if writer:
                writer.close()
                await writer.wait_closed()

    async def async_close(self) -> None:
        """Safely close the TCP connection, ensuring data flush."""

        if not self.writer:
            return

        _LOGGER.debug("Starting TCP Shutdown")
        try:
            # 1. Ensure that any remaining queued data is sent.
            await self.writer.drain()

            # 2. Let the peer know we are closing our side of the stream.
            self.writer.close()

            # 3. Wait for the OS socket resources to be released.
            await self.writer.wait_closed()
            _LOGGER.info("AAP TCP Connection Closed")

        except Exception as e:
            _LOGGER.debug("Error during AAP TCP Shutdown. %s", e)

        finally:
            # 4. Release the object references.
            self.writer = None
            self.reader = None

    async def async_send_status(self) -> None:
        """Sends the status command to the panel."""
        await self.async_send_command(CMD_STATUS)

    async def async_send_command(self, cmd: str) -> None:
        """Sends the command to the panel."""

        if not self.writer:
            raise ConnectionError(
                f"Cannot send command {cmd}: writer not available", cmd
            )

        command = f"{cmd}\n"
        command_bytes = command.encode("ascii")
        self.writer.write(command_bytes)

    async def listen_to_socket(self) -> None:
        """Continuously read data from the panel socket."""
        if not self.reader or not self.writer:
            _LOGGER.error("Listener called without active stream.")
            raise ConnectionError("Listener called without active stream.")

        while True:
            data = await self.reader.read(512)
            if not data:
                break
