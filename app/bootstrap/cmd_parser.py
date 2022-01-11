import argparse
from app.datastructures import Flags
from app.exceptions import CommandParserException

__all__ = ["process_cmd_args"]


class ErrorCatchingArgumentParser(argparse.ArgumentParser):
    """Overriding class to capture parser exceptions

    Args:
        argparse (ArgumentParser): Argument Parser
    """

    def exit(self, status=0, message=None):
        if status != 0:
            raise CommandParserException(message)
        raise SystemExit(status)


def process_cmd_args() -> Flags:
    """Capture and process the user supplied command line args

    Returns:
        Flags: Processed args
    """
    parser = ErrorCatchingArgumentParser(
        prog="overwatch", description="Seizure Detector Server"
    )

    parser.add_argument(
        "--log-level",
        default="warning",
        choices=["critical", "error", "warn", "warning", "info", "debug", "trace"],
        help="Application log level",
    )
    parser.add_argument(
        "-c", "--config", default="config.toml", help="Path to config.toml file"
    )
    parser.add_argument(
        "-s", "--silent", action="store_true", help="Silence all alerts"
    )
    parser.add_argument(
        "-t", "--test", action="store_true", help="Run the application in test mode"
    )
    parser.add_argument(
        "--file", default=None, help="Load video from file path instead of camera"
    )
    args = parser.parse_args()
    return Flags(
        silent=args.silent,
        config_path=args.config,
        test=args.test,
        log_level=args.log_level,
        file=args.file,
    )
