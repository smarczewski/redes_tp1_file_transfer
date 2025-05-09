from lib.argument_parser import *
from pathlib import Path
from socket import *
from lib.rdt_shared import *
import time

argsparser = ArgumentParser(ParserType.UPLOAD)
args = argsparser.get_args(ParserType.UPLOAD)

if args.protocol:
    from lib.rdt_sr import send_file_sr
else:
    from lib.rdt_sw import send_file_sw

verbose_print(f"Establishing connection to server...", True)

udp_socket = socket(AF_INET, SOCK_DGRAM)
udp_socket.settimeout(HANDSHAKE_TIMEOUT)

response_type, receiver_address = send_handshake(
    udp_socket, Type.UPLOAD, (args.host, args.port), args.name, args.verbose
)

if response_type == Type.ACK:
    # Server nos devolvió el ACK, y podemos continuar normalmente
    start_time = time.time()
    if args.protocol:
        udp_socket.settimeout(SENDER_TIMEOUT_SR)
        verbose_print(f"Upload using SELECTIVE REPEAT started", True)
        send_file_sr(
            udp_socket, args.src + "/" + args.name, receiver_address, args.verbose
        )
    else:
        udp_socket.settimeout(RECEIVER_TIMEOUT_SW)
        verbose_print(f"Upload using STOP AND WAIT started", True)
        send_file_sw(
            udp_socket, args.src + "/" + args.name, receiver_address, args.verbose
        )

    end_time = time.time()
    verbose_print(f"Upload time: {end_time - start_time}", True)

if response_type == Type.ERROR:
    # Hubo algún error
    udp_socket.close()
    exit(1)
