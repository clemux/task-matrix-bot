#!/usr/bin/env python3
import asyncio
import logging
import sys
from time import sleep

from aiohttp import ClientConnectionError, ServerDisconnectedError
from nio import (
    AsyncClient,
    AsyncClientConfig,
    InviteMemberEvent,
    LocalProtocolError,
    LoginError,
    MegolmEvent,
    RoomMessageText,
    UnknownEvent,
)

from taskbot.callbacks import Callbacks
from taskbot.config import Config
from taskbot.errors import ConfigError
from taskbot.storage import Storage

logger = logging.getLogger(__name__)


async def run_bot():
    """The first function that is run when starting the bot"""

    # Read user-configured options from a config file.
    # A different config file path can be specified as the first command line argument
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        config_path = "config.yaml"

    # Read the parsed config file and create a Config object
    try:
        config = Config(config_path)
    except ConfigError:
        logger.error(f"Could not load configuration file '{config_path}'")
        sys.exit(1)

    # Configure the database
    store = Storage(config.database)

    # Configuration options for the AsyncClient
    client_config = AsyncClientConfig(
        max_limit_exceeded=0,
        max_timeouts=0,
        store_sync_tokens=True,
        encryption_enabled=True,
    )

    # Initialize the matrix client
    client = AsyncClient(
        config.homeserver_url,
        config.user_id,
        device_id=config.device_id,
        store_path=config.store_path,
        config=client_config,
    )

    if config.user_token:
        client.access_token = config.user_token
        client.user_id = config.user_id

    # Set up event callbacks
    callbacks = Callbacks(client, store, config)

    client.add_event_callback(callbacks.decryption_failure, (MegolmEvent,))

    try:
        if config.user_token:
            # Use token to log in
            client.load_store()

            # Sync encryption keys with the server
            if client.should_upload_keys:
                await client.keys_upload()
        else:
            # Try to login with the configured username/password
            try:
                login_response = await client.login(
                    password=config.user_password,
                    device_name=config.device_name,
                )

                # Check if login failed
                if type(login_response) == LoginError:
                    logger.error("Failed to login: %s", login_response.message)
                    return False
            except LocalProtocolError as e:
                # There's an edge case here where the user hasn't installed the correct C
                # dependencies. In that case, a LocalProtocolError is raised on login.
                logger.fatal(
                    "Failed to login. Have you installed the correct dependencies? "
                    "https://github.com/poljar/matrix-nio#installation "
                    "Error: %s",
                    e,
                )
                return False

            # Login succeeded!

        logger.info(f"Logged in as {config.user_id}")
        await client.sync()
        client.add_event_callback(callbacks.unknown, (UnknownEvent,))
        client.add_event_callback(callbacks.message, (RoomMessageText,))
        client.add_event_callback(
            callbacks.invite_event_filtered_callback, (InviteMemberEvent,)
        )
        await client.sync_forever(timeout=30000, full_state=True)

    except (ClientConnectionError, ServerDisconnectedError):
        logger.error("Unable to connect to homeserver.")

    finally:
        # Make sure to close the client connection on disconnect
        await client.close()


def main():
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run_bot())
    except KeyboardInterrupt:
        logger.info('Exiting...')

if __name__ == '__main__':
    main()