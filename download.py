from lib.argument_parser import *
from pathlib import Path
from socket import *
from lib.rdt import *
import ipaddress

argsparser = ArgumentParser(ParserType.DOWNLOAD)
args = get_args(argsparser, ParserType.DOWNLOAD)

udp_socket = socket(AF_INET, SOCK_DGRAM)
response_type, _ = establish_connection(
    udp_socket, Type.DOWNLOAD, (args.host, args.port), args.name
)

if response_type == Type.ACK:
    # Server nos devolvió el ACK, y podemos continuar normalmente
    if args.protocol:
        # recv_file_sr(udp_socket, args.name)
        pass
    udp_socket.settimeout(RECEIVER_TIMEOUT_SW)
    recv_file_sw(udp_socket, args.dst + "/" + args.name)

if response_type == Type.ERROR:
    # Hubo algún error
    udp_socket.close()
    exit(1)
