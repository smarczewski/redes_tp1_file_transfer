import argparse

class ArgumentParser:
    def __init__(self, type: str):
        self.type = type
        self.create_parser()
        self.add_arguments()

        self.args = self.parser.parse_args()

    def create_parser(self):
        """Create and configure the argument parser"""
        if self.type == 'client':
            usage = '%(prog)s [-h] [-v | -q] [-H ADDR] [-p PORT] [-s FILEPATH] [-n FILENAME] [-r protocol]'
        elif self.type == 'server':
            usage = '%(prog)s [-h] [-v | -q] [-H ADDR] [-p PORT] [-s DIRPATH] [-r protocol]'

        self.parser = argparse.ArgumentParser(
            usage=usage,
            description='<command description>',
        )
        self.parser._optionals.title = 'optional arguments'
        
    def add_arguments(self):
        """Add common arguments for both client and server"""
        # Verbosity options (mutually exclusive)
        group = self.parser.add_mutually_exclusive_group()
        group.add_argument('-v', '--verbose', action='store_true', 
                        help='increase output verbosity')
        group.add_argument('-q', '--quiet', action='store_true', 
                        help='decrease output verbosity')
        
        # Connection options
        self.parser.add_argument('-H', '--host', metavar='', default='localhost',
                        help='server IP address')
        self.parser.add_argument('-p', '--port', metavar='', type=int, default=8080,
                        help='server port')
        
        if self.type == 'client':
            self.add_client_arguments()
        elif self.type == 'server':
            self.add_server_arguments()

        # Error Recovery Protocol option
        self.parser.add_argument('-r', '--protocol', metavar='',
                        help='error recovery protocol')
        
    def add_client_arguments(self):
        """Add client-specific arguments"""
        # File options
        self.parser.add_argument('-s', '--src', metavar='',
                        help='source file path')
        self.parser.add_argument('-n', '--name', metavar='',
                        help='file name')
        
    def add_server_arguments(self):
        """Add server-specific arguments"""
        # Server-specific options can be added here
        self.parser.add_argument('-s', '--storage', metavar='',
                        help='storage dir path')
    
