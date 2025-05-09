import argparse
from enum import Enum
import ipaddress
from pathlib import Path

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8080


class ParserType(Enum):
    UPLOAD = 0
    DOWNLOAD = 1
    SERVER = 2


class ArgumentParser:
    def __init__(self, type: ParserType):
        self.type = type
        self.create_parser()
        self.add_arguments()

        self.args = self.parser.parse_args()

    def create_parser(self):
        """Create and configure the argument parser"""
        if self.type == ParserType.UPLOAD:
            usage = "%(prog)s [-h] [-v | -q] [-H ADDR] [-p PORT] [-s FILEPATH] [-n FILENAME] [-r protocol]"
        elif self.type == ParserType.DOWNLOAD:
            usage = "%(prog)s [-h] [-v | -q] [-H ADDR] [-p PORT] [-d FILEPATH] [-n FILENAME] [-r protocol]"
        elif self.type == ParserType.SERVER:
            usage = (
                "%(prog)s [-h] [-v | -q] [-H ADDR] [-p PORT] [-s DIRPATH] [-r protocol]"
            )

        self.parser = argparse.ArgumentParser(
            usage=usage,
            description="<command description>",
        )
        self.parser._optionals.title = "optional arguments"

    def add_arguments(self):
        """Add common arguments for both client and server"""
        # Verbosity options (mutually exclusive)
        group = self.parser.add_mutually_exclusive_group()
        group.add_argument(
            "-v", "--verbose", action="store_true", help="increase output verbosity"
        )
        group.add_argument(
            "-q", "--quiet", action="store_true", help="decrease output verbosity"
        )

        # Connection options
        self.parser.add_argument(
            "-H", "--host", metavar="", default=DEFAULT_HOST, help="server IP address"
        )
        self.parser.add_argument(
            "-p",
            "--port",
            metavar="",
            type=int,
            default=DEFAULT_PORT,
            help="server port",
        )

        if self.type == ParserType.SERVER:
            self.add_server_arguments()
        else:
            self.add_client_arguments()

        # Error Recovery Protocol option
        self.parser.add_argument(
            "-r",
            "--protocol",
            action="store_true",
            default=False,
            help="error recovery protocol",
        )

    def add_client_arguments(self):
        """Add client-specific arguments"""
        # File options
        if self.type == ParserType.UPLOAD:
            self.parser.add_argument("-s", "--src", metavar="", help="source file path")
        else:
            self.parser.add_argument(
                "-d", "--dst", metavar="", help="destination file path"
            )

        self.parser.add_argument("-n", "--name", metavar="", help="file name")

    def add_server_arguments(self):
        """Add server-specific arguments"""
        # Server-specific options can be added here
        self.parser.add_argument("-s", "--storage", metavar="", help="storage dir path")

    def get_args(self, app):

        if not is_valid_ip_address(self.args.host):
            self.parser.exit(1, message="ERROR: The IP address is not valid\n")

        if not is_valid_port(self.args.port):
            self.parser.exit(1, message="ERROR: The port is not valid\n")

        if app == ParserType.SERVER:
            if not Path(self.args.storage).exists():
                self.parser.exit(
                    1, message="ERROR: The storage directory path doesn't exist\n"
                )

        elif app == ParserType.UPLOAD:
            if not Path(self.args.src).exists():
                self.parser.exit(
                    1, message="ERROR: The source file path doesn't exist\n"
                )
            if not Path(self.args.src + "/" + self.args.name).exists():
                self.parser.exit(
                    1, message=f"ERROR: The file {self.args.name} doesn't exist\n"
                )

        else:
            if not Path(self.args.dst).exists():
                self.parser.exit(
                    1, message="ERROR: The destination file path doesn't exist\n"
                )
            if Path(self.args.dst + "/" + self.args.name).exists():
                self.parser.exit(
                    1,
                    message=f"ERROR: A file named {self.args.name} already exists\n",
                )

        return self.args


def is_valid_ip_address(address):
    try:
        if address == DEFAULT_HOST:
            pass
        else:
            ipaddress.ip_address(address)
        return True
    except ValueError:
        return False


def is_valid_port(port):
    return 1023 < port <= 65535


# Recheck
