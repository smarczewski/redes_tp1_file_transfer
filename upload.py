from lib.argument_parser import *
from pathlib import Path
from socket import *
from lib.rdt import *
import ipaddress

argsparser = ArgumentParser(ParserType.UPLOAD)
args = get_args(argsparser, ParserType.UPLOAD)

udp_socket = socket(AF_INET, SOCK_DGRAM)
udp_socket.settimeout(RECEIVER_TIMEOUT_SW)

response_type, receiver_address = send_handshake(
    udp_socket, Type.UPLOAD, (args.host, args.port), args.name
)

if response_type == Type.ACK:
    # Server nos devolvió el ACK, y podemos continuar normalmente
    start_time = time.time()
    if args.protocol:
        udp_socket.settimeout(SENDER_TIMEOUT_SR)
        send_file_sr(udp_socket, args.src + "/" + args.name, receiver_address)
    else:
        send_file_sw(udp_socket, args.src + "/" + args.name, receiver_address)

    end_time = time.time()
    print(f"TIME: {end_time - start_time}")

if response_type == Type.ERROR:
    # Hubo algún error
    udp_socket.close()
    exit(1)
