"""Handles the back and forth between the alarm panel and home assistant."""

from __future__ import annotations

import asyncio
import logging

import const

_LOGGER = logging.getLogger(__name__)


class ArrowheadAPI:
    """Defines methods for communication with Arrowhead Alarm panel."""

    def __init__(self, host: str, port: int) -> None:
        """Create the API task defining the requried parameters."""
        self.host = host
        self.port = port
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None

    @classmethod
    async def create(cls, host: str, port: int) -> ArrowheadAPI:
        """Factory method to create and connect the API instance."""

        instance = cls(host, port)
        instance.reader, instance.writer = await asyncio.open_connection(host, port)
        return instance

    @staticmethod
    def validate_set_mode(host: str, port: int) -> bool:
        """Confirms connnection available and sets panel to Mode 2.

        Returns:
            bool: True if connection succesful and MODE 2 response recieved. Otherwise False
        """
        # Seconds to wait for validation process.

        instance = ArrowheadAPI(host, port)
        TIMEOUT = 5.0
        try:
            # Use asyncio.run() to execute the asynchronous core function synchronously
            return asyncio.run(instance._async_validate_mode(host, port, TIMEOUT))
        except TimeoutError:
            _LOGGER.debug("Validation of AAP Connection failed due to timeout error")
            return False
        except Exception as e:  # noqa: BLE001
            _LOGGER.debug("Validation of AAP Connection failed due to exception: {e}")
            return False

    async def _async_validate_mode(
        self, host: str, port: int, timeout: float = 5, mode: int = 2
    ) -> bool:
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
            mode_command = f"{const.CMD_MODE} {mode}{const.MODE_1_DELIMITER[1]}"
            cmd = mode_command.encode("ascii")
            writer.write(cmd)
            await writer.drain()

            # 3. Read the response (or time out). 512 is the maximum byte length returned from the panel.
            buffer = b""
            while True:
                d_chunk = await asyncio.wait_for(reader.read(512), timeout=timeout)

                if not d_chunk:
                    _LOGGER.debug(
                        "Connection closed by panel before mode response recieved"
                    )
                    return False

                buffer += d_chunk

                if expected_response in buffer:
                    return True

                if len(buffer) > 8192:
                    _LOGGER.debug("Validation buffer exceeded 8kb")
                    return False
        finally:
            if writer:
                writer.close()
                await writer.wait_closed()

    async def async_close(self) -> None:
        """Safely close the TCP connection, ensuring data flush."""

        if not self.writer:
            return

        _LOGGER.debug("Starting TCP Shutdown...")
        try:
            # 1. Ensure that any remaining queued data is sent.
            await self.writer.drain()

            # 2. Let the peer know we are closing our side of the stream.
            self.writer.close()

            # 3. Wait for the OS socket resources to be released.
            await self.writer.wait_closed()
            _LOGGER.info("AAP TCP Connection Closed.")

        except Exception as e:
            _LOGGER.debug("Error during AAP TCP Shutdown. %s", e)

        finally:
            # 4. Release the object references.
            self.writer = None
            self.reader = None

    async def async_send_status(self) -> None:
        """Sends the status command to the panel."""
        await self.async_send_command(const.CMD_STATUS)

    async def async_send_command(self, cmd: str) -> None:
        """Sends the command to the panel."""

        if not self.writer:
            raise ConnectionError("Cannot send command %s: writer not available", cmd)

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
