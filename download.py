from lib.argument_parser import *
from pathlib import Path
from socket import *
from lib.rdt_shared import *
import time

argsparser = ArgumentParser(ParserType.DOWNLOAD)
args = get_args(argsparser, ParserType.DOWNLOAD)

if args.protocol:
    from lib.rdt_sr import recv_file_sr
else:
    from lib.rdt_sw import recv_file_sw


udp_socket = socket(AF_INET, SOCK_DGRAM)
udp_socket.settimeout(RECEIVER_TIMEOUT_SW)
response_type, _ = send_handshake(
    udp_socket, Type.DOWNLOAD, (args.host, args.port), args.name
)

if response_type == Type.ACK:
    # Server nos devolvió el ACK, y podemos continuar normalmente
    start_time = time.time()
    if args.protocol:
        udp_socket.settimeout(RECEIVER_TIMEOUT_SR)
        recv_file_sr(udp_socket, args.dst + "/" + args.name)
    else:
        recv_file_sw(udp_socket, args.dst + "/" + args.name)

    end_time = time.time()
    print(f"TIME: {end_time - start_time}")

if response_type == Type.ERROR:
    # Hubo algún error
    udp_socket.close()
    exit(1)
