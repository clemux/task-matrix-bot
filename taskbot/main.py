#!/usr/bin/env python3
import argparse
import asyncio
import logging
import sys
from getpass import getpass

from aiohttp import ClientConnectionError, ServerDisconnectedError
from nio import (
    AsyncClient,
    AsyncClientConfig,
    LoginError,
    MegolmEvent,
    RoomMessageText,
    UnknownEvent, )

from taskbot.callbacks import Callbacks
from taskbot.config import Config
from taskbot.errors import ConfigError

logger = logging.getLogger(__name__)


async def run_bot(args):
    """The first function that is run when starting the bot"""

    # Read user-configured options from a config file.
    # A different config file path can be specified as the first command line argument
    config_path = args.config_path
    # Read the parsed config file and create a Config object
    try:
        config = Config(config_path)
    except ConfigError as e:
        logger.error(f"Could not load config: {e}")
        sys.exit(1)

    if not config.user_token and not config.user_password:
        raise ConfigError("Must supply either user token or password.")

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
    callbacks = Callbacks(client, config)

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
            except Exception as e:
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

        response = await client.sync()
        if getattr(response, 'status_code', None) is not None and response.status_code == 'M_UNKNOWN_TOKEN':
            logger.error("Invalid access token. Run the login command and set matrix.user_token again")
            return False

        client.add_event_callback(callbacks.decryption_failure, (MegolmEvent,))
        client.add_event_callback(callbacks.unknown, (UnknownEvent,))
        client.add_event_callback(callbacks.message, (RoomMessageText,))
        await client.sync_forever(timeout=30000, full_state=True)

    except (ClientConnectionError, ServerDisconnectedError):
        logger.error("Unable to connect to homeserver.")

    finally:
        # Make sure to close the client connection on disconnect
        await client.close()


async def login(args):
    config_path = args.config_path
    # Read the parsed config file and create a Config object
    try:
        config = Config(config_path)
    except ConfigError as e:
        logger.error(f"Could not load config: {e}")
        sys.exit(1)

    # Configuration options for the AsyncClient
    client_config = AsyncClientConfig(
        max_limit_exceeded=0,
        max_timeouts=0,
        store_sync_tokens=True,
        encryption_enabled=True,
    )

    logger.info(f'Logging in as user {config.user_id}')
    user_password = config.user_password
    if user_password is None:
        print('No password set in configuration file.')
        user_password = getpass()
    else:
        print("Using password set in configuration file.")
    client = AsyncClient(
        config.homeserver_url,
        config.user_id,
        device_id=config.device_id,
        store_path=config.store_path,
        config=client_config,
    )
    try:
        login_response = await client.login(
            password=user_password,
            device_name=config.device_name,
        )
        print("Access token:", login_response.access_token)
        print(f"You can now edit {config_path} and set 'matrix.user_token'")
    finally:
        await client.close()


def main():
    parser = argparse.ArgumentParser()
    sub_parsers = parser.add_subparsers(required=True)

    # run bot
    run_parser = sub_parsers.add_parser('run')
    run_parser.add_argument('config_path')
    run_parser.set_defaults(cmd='run')

    # login
    login_parser = sub_parsers.add_parser('login')
    login_parser.add_argument('config_path')
    login_parser.set_defaults(cmd='login')
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    if args.cmd == 'run':
        try:
            loop.run_until_complete(run_bot(args))
        except KeyboardInterrupt:
            logger.info('Exiting...')
    elif args.cmd == 'login':
        loop.run_until_complete(login(args))


if __name__ == '__main__':
    main()
