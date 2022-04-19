import logging
import sys

from nio import (
    AsyncClient,
    MatrixRoom,
    MegolmEvent,
    RoomMessageText,
    UnknownEvent,
)

from taskbot.chat_functions import send_text_to_room
from taskbot.commands import task_commands
from taskbot.config import Config
from taskbot.message_responses import Message

logger = logging.getLogger(__name__)


class Callbacks:
    def __init__(self, client: AsyncClient, config: Config):
        """
        Args:
            client: nio client used to interact with matrix.

            config: Bot configuration parameters.
        """
        self.client = client
        self.config = config

    async def message(self, room: MatrixRoom, event: RoomMessageText) -> None:
        """Callback for when a message event is received

        Args:
            room: The room the event came from.

            event: The event defining the message.
        """
        # Extract the message text
        msg = event.body

        # Ignore messages from ourselves
        if event.sender == self.client.user:
            return

        logger.debug(
            f"Bot message received for room {room.display_name} | "
            f"{room.user_name(event.sender)}: {msg}"
        )

        # room.is_group is often a DM, but not always.
        # room.is_group does not allow room aliases
        # room.member_count > 2 ... we assume a public room
        # room.member_count <= 2 ... we assume a DM
        if room.member_count > 2:
            # General message listener
            message = Message(self.client, self.config, msg, room, event)
            await message.process()
            return

        # Otherwise if this is in a 1-1 with the bot,
        # treat it as a command

        cmd, _, args = msg.partition(' ')
        cmd = cmd.lower()
        if not cmd in task_commands:
            response = f"Unknown command '{cmd}'"
        else:
            cmd = task_commands.get(cmd)()
            response = await cmd.process(args)
        await send_text_to_room(self.client, room.room_id, message=response)

    async def decryption_failure(self, room: MatrixRoom, event: MegolmEvent) -> None:
        """Callback for when an event fails to decrypt. Inform the user.

        Args:
            room: The room that the event that we were unable to decrypt is in.

            event: The encrypted event that we were unable to decrypt.
        """
        logger.error(
            f"Failed to decrypt event '{event.event_id}' in room '{room.room_id}'!"
            f"\n\n"
            f"Tip: try using a different device ID in your config file and restart."
            f"\n\n"
            f"If all else fails, delete your store directory and let the bot recreate "
            f"it (your reminders will NOT be deleted, but the bot may respond to existing "
            f"commands a second time)."
        )

        sys.exit(1)

    async def unknown(self, room: MatrixRoom, event: UnknownEvent) -> None:
        logger.debug(
            f"Got unknown event with type to {event.type} from {event.sender} in {room.room_id}."
        )
