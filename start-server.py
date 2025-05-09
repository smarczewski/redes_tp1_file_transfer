from lib.argument_parser import *
from lib.rdt_shared import *
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from socket import *

N_THREADS = 10


def initial_server_response(request_type, filepath, seq_number):
    error_packet = Type.ERROR.value.to_bytes(TYPE_SIZE, "big") + seq_number.to_bytes(
        SEQ_NUMBER_SIZE, "big"
    )
    if request_type == Type.DOWNLOAD:
        if not Path(filepath).exists():
            error_msg = f"The server storage doesn't contain the file: {filename}"
            return error_packet + error_msg.encode()
    elif request_type == Type.UPLOAD:
        if Path(filepath).exists():
            error_msg = f"The server storage already contains a file named: {filename}"
            return error_packet + error_msg.encode()
    ack_packet = Type.ACK.value.to_bytes(TYPE_SIZE, "big") + seq_number.to_bytes(
        SEQ_NUMBER_SIZE, "big"
    )
    return ack_packet


def handle_connection(filepath, request_type, request_seq_number, client_address):
    new_udp_socket = socket(AF_INET, SOCK_DGRAM)
    new_udp_socket.bind((args.host, 0))

    packet_to_send = initial_server_response(request_type, filepath, request_seq_number)

    client_response = recv_handshake(
        new_udp_socket, request_type, client_address, packet_to_send
    )

    # Si recv_handshake nos devuelve algo distinto a ACK, algo salió mal
    if client_response != Type.ACK:
        new_udp_socket.close()
        return

    if request_type == Type.DOWNLOAD:
        if args.protocol:
            new_udp_socket.settimeout(RECEIVER_TIMEOUT_SR)
            send_file_sr(new_udp_socket, filepath, client_address)
        else:
            new_udp_socket.settimeout(SENDER_TIMEOUT_SW)
            send_file_sw(new_udp_socket, filepath, client_address, args.verbose)

    elif request_type == Type.UPLOAD:
        if args.protocol:
            new_udp_socket.settimeout(RECEIVER_TIMEOUT_SR)
            recv_file_sr(new_udp_socket, filepath)
        else:
            new_udp_socket.settimeout(RECEIVER_TIMEOUT_SW)
            recv_file_sw(new_udp_socket, filepath, args.verbose)

    new_udp_socket.close()


argsparser = ArgumentParser(ParserType.SERVER)
args = get_args(argsparser, ParserType.SERVER)

if args.protocol:
    from lib.rdt_sr import recv_file_sr, send_file_sr
else:
    from lib.rdt_sw import recv_file_sw, send_file_sw

udp_sv_socket = socket(AF_INET, SOCK_DGRAM)
udp_sv_socket.bind((args.host, args.port))

with ThreadPoolExecutor(max_workers=N_THREADS) as pool:

    while True:
        print("Listening for connections...")
        request_from_client, client_address = udp_sv_socket.recvfrom(PACKET_SIZE)
        request_type, request_seq_number = get_header(request_from_client)
        filename = get_payload(request_from_client).decode()
        filepath = args.storage + "/" + filename

        pool.submit(
            handle_connection,
            filepath,
            request_type,
            request_seq_number,
            client_address,
        )
