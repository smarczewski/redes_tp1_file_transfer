from enum import Enum

TYPE_SIZE = 1
SEQ_NUMBER_SIZE = 2
PAYLOAD_SIZE = 4096
HEADER_SIZE = TYPE_SIZE + SEQ_NUMBER_SIZE
PACKET_SIZE = TYPE_SIZE + SEQ_NUMBER_SIZE + PAYLOAD_SIZE


class Type(Enum):
    DOWNLOAD = 0
    UPLOAD = 1
    ACK = 2
    DATA = 3
    CLOSE = 4
    ERROR = 5


def get_header(packet):
    type = Type(int.from_bytes(packet[:TYPE_SIZE], "big"))
    seq_number = int.from_bytes(packet[TYPE_SIZE:HEADER_SIZE], "big")

    return type, seq_number


def get_payload(packet):
    payload = packet[HEADER_SIZE:]

    return payload


def send_ack(seq_number, socket, address):
    ack_packet = Type.ACK.value.to_bytes(TYPE_SIZE, "big") + seq_number.to_bytes(
        SEQ_NUMBER_SIZE, "big"
    )
    socket.sendto(ack_packet, address)


def send_error(seq_number, socket, address, error_msg):
    ack_packet = (
        Type.ERROR.value.to_bytes(TYPE_SIZE, "big")
        + seq_number.to_bytes(SEQ_NUMBER_SIZE, "big")
        + error_msg.encode()
    )
    socket.sendto(ack_packet, address)


def establish_connection(
    udp_socket, connection_type: Type, address_to_connect, filename
):
    initial_seq = 0
    initial_packet = (
        connection_type.value.to_bytes(TYPE_SIZE, "big")
        + initial_seq.to_bytes(SEQ_NUMBER_SIZE, "big")
        + filename.encode()
    )

    udp_socket.sendto(initial_packet, address_to_connect)
    response_from_server, server_address = udp_socket.recvfrom(PACKET_SIZE)

    response_type, _ = get_header(response_from_server)
    if response_type == Type.ERROR:
        error_msg = get_payload(response_from_server).decode()
        print(f"ERROR: {error_msg}")

    return response_type, server_address


def recv_file_sw(udp_socket, filepath):
    response_type = Type.ACK
    packet_counter = 0
    file = open(filepath, "ab")

    # Mientras el tipo no sea CLOSE
    while response_type != Type.CLOSE:
        # Leo del socket:
        response_from_server, server_address = udp_socket.recvfrom(PACKET_SIZE)
        response_type, response_seq_number = get_header(response_from_server)

        # Si lo que llego es tipo DATA y su secuencia es igual a counter:
        if response_type == Type.DATA:
            if response_seq_number == packet_counter:
                print(f"Received packet #{response_seq_number} correctly")
                # Es el que esperabamos y lo escribimos a archivo
                # mandamos ACK de su numero de secuencia
                # y aumentamos counter
                payload = get_payload(response_from_server)
                file.write(payload)
                file.flush()
                send_ack(packet_counter, udp_socket, server_address)
                packet_counter += 1

            else:
                # reenviamos ACK de nuestro counter
                print(
                    f"Received packet #{response_seq_number} but expected {packet_counter}"
                )
                send_ack(packet_counter, udp_socket, server_address)

    print(f"Received CLOSE packet")
    file.close()


def send_file_sw(udp_socket, filepath, receiver_address):
    packet_counter = 0
    file = open(filepath, "rb")
    data_read = file.read(PAYLOAD_SIZE)

    # Mientras el tipo no sea CLOSE
    while data_read:
        print(f"Sent packet #{packet_counter}")
        data_packet = (
            Type.DATA.value.to_bytes(TYPE_SIZE, "big")
            + packet_counter.to_bytes(SEQ_NUMBER_SIZE, "big")
            + data_read
        )
        udp_socket.sendto(data_packet, receiver_address)

        # Leo del socket:
        response_from_receiver, receiver_address = udp_socket.recvfrom(PACKET_SIZE)
        response_type, response_seq_number = get_header(response_from_receiver)

        # Si lo que llego es tipo ACK:
        if response_type == Type.ACK:
            # Si es ACK que esperabamos, enviamos el siguiente
            if response_seq_number == packet_counter:
                print(f"Received expected ACK #{response_seq_number}")
                data_read = file.read(PAYLOAD_SIZE)
                packet_counter += 1
            else:
                print(
                    f"Received unexpected ACK #{response_seq_number}, resending previous packet #{packet_counter}"
                )

    print("Sent CLOSE packet")
    close_packet = Type.CLOSE.value.to_bytes(
        TYPE_SIZE, "big"
    ) + packet_counter.to_bytes(SEQ_NUMBER_SIZE, "big")
    udp_socket.sendto(close_packet, receiver_address)
    file.close()


def send_file_sr(udp_socket, filepath, receiver_address):
    pass


def recv_file_sr(udp_socket, filepath, receiver_address):
    pass
