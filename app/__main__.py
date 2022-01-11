import asyncio
from concurrent.futures import ProcessPoolExecutor
from contextlib import suppress
from signal import SIGINT, SIGTERM
from loguru import logger
import uvloop
from app.bootstrap import initialise
from app.exceptions import OverwatchException
from app.events import Event, Publisher, Topic
from app.system import run_system_tasks


def signal_handler(sig, publisher: Publisher, process_pool: ProcessPoolExecutor):
    logger.debug(f"Got {str(sig)} signal")
    logger.info("Shutting down...")
    publisher.send_message(Topic.SYSTEM_SHUTDOWN, Event())
    loop_ = asyncio.get_event_loop()
    tasks = asyncio.all_tasks()
    logger.debug("Cancelling tasks")
    process_pool.shutdown(wait=True, cancel_futures=True)
    for task in tasks:
        task.cancel()
    loop_.remove_signal_handler(SIGTERM)
    loop_.add_signal_handler(SIGINT, lambda: None)


def set_sig_handlers(publisher: Publisher, process_pool: ProcessPoolExecutor):
    loop_ = asyncio.get_event_loop()
    for sig in (SIGINT, SIGTERM):
        loop_.add_signal_handler(sig, signal_handler, sig, publisher, process_pool)


async def main():
    with suppress(asyncio.CancelledError):  # TODO: Needed here?
        config = initialise()
        if config.flags.test:
            logger.warning("Running in test mode")
        if config.flags.silent:
            logger.warning("Running in silent mode")
        publisher = Publisher()
        process_pool = ProcessPoolExecutor()
        set_sig_handlers(publisher, process_pool)
        await run_system_tasks(config, publisher, process_pool)


if __name__ == "__main__":
    print("Starting Overwatch Server........")
    try:
        uvloop.install()
        if __debug__:
            print("Running in debug mode, run with python flag -O to disable mode")
        asyncio.run(main())
    except OverwatchException as ex:  # Top level exception handler
        print(ex)
        raise SystemExit(2) from ex
    else:
        raise SystemExit(0)
