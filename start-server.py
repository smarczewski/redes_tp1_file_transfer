from lib.argument_parser import *
from lib.rdt import *
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from socket import *

N_THREADS = 10


def handle_connection(filepath, request_type, request_seq_number, client_address):
    new_udp_socket = socket(AF_INET, SOCK_DGRAM)
    new_udp_socket.bind((args.host, 0))

    send_ack(request_seq_number, new_udp_socket, client_address)

    if request_type == Type.DOWNLOAD:
        if args.protocol:
            new_udp_socket.settimeout(RECEIVER_TIMEOUT_SR)
            send_file_sr(new_udp_socket, filepath, client_address)
            pass
        else:
            new_udp_socket.settimeout(SENDER_TIMEOUT_SW)
            send_file_sw(new_udp_socket, filepath, client_address)

    elif request_type == Type.UPLOAD:
        if args.protocol:
            new_udp_socket.settimeout(RECEIVER_TIMEOUT_SR)
            recv_file_sr(new_udp_socket, filepath)
            pass
        else:
            new_udp_socket.settimeout(RECEIVER_TIMEOUT_SW)
            recv_file_sw(new_udp_socket, filepath)

    new_udp_socket.close()


argsparser = ArgumentParser(ParserType.SERVER)
args = get_args(argsparser, ParserType.SERVER)

udp_sv_socket = socket(AF_INET, SOCK_DGRAM)
udp_sv_socket.bind((args.host, args.port))

with ThreadPoolExecutor(max_workers=N_THREADS) as pool:

    while True:
        request_from_client, client_address = udp_sv_socket.recvfrom(PACKET_SIZE)
        request_type, request_seq_number = get_header(request_from_client)
        filename = get_payload(request_from_client).decode()
        filepath = args.storage + "/" + filename

        if request_type == Type.DOWNLOAD:
            if not Path(filepath).exists():
                error_msg = f"The server storage doesn't contain the file: {filename}"
                send_error(request_seq_number, udp_sv_socket, client_address, error_msg)
        elif request_type == Type.UPLOAD:
            if Path(filepath).exists():
                error_msg = (
                    f"The server storage already contains a file named: {filename}"
                )
                send_error(request_seq_number, udp_sv_socket, client_address, error_msg)

        pool.submit(
            handle_connection,
            filepath,
            request_type,
            request_seq_number,
            client_address,
        )
