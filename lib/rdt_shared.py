from enum import Enum
from socket import *

TYPE_SIZE = 1
SEQ_NUMBER_SIZE = 2
PAYLOAD_SIZE = 4096
HEADER_SIZE = TYPE_SIZE + SEQ_NUMBER_SIZE
PACKET_SIZE = TYPE_SIZE + SEQ_NUMBER_SIZE + PAYLOAD_SIZE

SENDER_TIMEOUT_SW = 0.03
RECEIVER_TIMEOUT_SW = 0.03

SENDER_TIMEOUT_SR = 0.05
RECEIVER_TIMEOUT_SR = 0.05

WINDOW_SIZE = 32


MAX_TRIES = 15


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
    print(f"Sent ACK #{seq_number}")
    socket.sendto(ack_packet, address)


def send_error(seq_number, socket, address, error_msg):
    error_packet = (
        Type.ERROR.value.to_bytes(TYPE_SIZE, "big")
        + seq_number.to_bytes(SEQ_NUMBER_SIZE, "big")
        + error_msg.encode()
    )
    socket.sendto(error_packet, address)


def send_data(seq_number, socket, address, data):
    print(f"Sent packet #{seq_number}")
    data_packet = (
        Type.DATA.value.to_bytes(TYPE_SIZE, "big")
        + seq_number.to_bytes(SEQ_NUMBER_SIZE, "big")
        + data
    )
    socket.sendto(data_packet, address)


def send_close(seq_number, socket, address):
    print("Sent CLOSE packet")
    close_packet = Type.CLOSE.value.to_bytes(TYPE_SIZE, "big") + seq_number.to_bytes(
        SEQ_NUMBER_SIZE, "big"
    )

    n_tries = 0
    while n_tries < MAX_TRIES:
        n_tries += 1
        try:
            socket.sendto(close_packet, address)
            response_from_server, server_address = socket.recvfrom(PACKET_SIZE)
            response_type, _ = get_header(response_from_server)

            # Si nos devuelven ACK, recibieron el CLOSE
            if response_type == Type.ACK:
                return response_type, server_address

            raise TimeoutError
        except timeout:
            continue


def receive_ack(socket):
    response_from_receiver, _ = socket.recvfrom(PACKET_SIZE)
    return get_header(response_from_receiver)


def received_expected_ack(received_type, received_seq_number, expected_seq_number):
    if received_type == Type.ACK and received_seq_number == expected_seq_number:
        print(f"Received expected ACK #{received_seq_number}")
        return True
    print(
        f"Received unexpected ACK #{received_seq_number}, resending previous packet #{expected_seq_number}"
    )
    return False


def received_expected_data(received_type, received_seq_number, expected_seq_number):
    if received_type == Type.DATA:
        if received_seq_number == expected_seq_number:
            print(f"Received packet #{received_seq_number} correctly")
            return True
        print(
            f"Received packet #{received_seq_number} but expected #{expected_seq_number}"
        )
    return False


def send_handshake(udp_socket, connection_type: Type, address_to_connect, filename):
    # Intentamos hacerle llegar el paquete DOWNLOAD/UPLOAD al server
    response_type, server_address = establish_connection(
        udp_socket, connection_type, address_to_connect, filename
    )

    # Si el server nos responde con un ACK
    if response_type == Type.ACK:
        # en el caso de UPLOAD, ya empezamos a enviar DATA
        # y el server ya deberia estar escuchando en ese socket
        if connection_type == Type.UPLOAD:
            return response_type, server_address

    # Si el server nos responde directamente con DATA
    elif response_type == Type.DATA:
        # en el caso de DOWNLOAD significa que salio todo bien y ya estamos recibiendo DATA
        if connection_type == Type.DOWNLOAD:
            return Type.ACK, server_address
    else:
        # Si el server nos responde con un ERROR
        return Type.ERROR, server_address


def recv_handshake(
    udp_socket, connection_type: Type, address_to_connect, packet_to_send
):
    packet_to_send_type, _ = get_header(packet_to_send)

    # En el caso de UPLOAD enviamos ACK/ERROR
    if connection_type == Type.UPLOAD:
        response_type = receive_connection(
            packet_to_send, udp_socket, address_to_connect, Type.DATA
        )

        # Si el cliente nos devolvio DATA es porque esta todo bien
        if response_type == Type.DATA:
            return Type.ACK

        return Type.ERROR

    # En el caso de DOWNLOAD, si esta todo bien y no hay que mandar ERROR
    # empezamos a mandar la data directamente al cliente, lo que implicitamente
    # le avisa que esta todo bien
    elif packet_to_send_type == Type.ACK:
        return Type.ACK

    # Si al contrario hay que mandar un ERROR, simplemente lo hacemos y esperamos un ACK
    elif packet_to_send_type == Type.ERROR:
        response_type = receive_connection(
            packet_to_send, udp_socket, address_to_connect, Type.ACK
        )

        if response_type == Type.ACK:
            return Type.ERROR

    return Type.ERROR


def establish_connection(
    udp_socket, connection_type: Type, address_to_connect, filename
):
    initial_seq = 0
    initial_packet = (
        connection_type.value.to_bytes(TYPE_SIZE, "big")
        + initial_seq.to_bytes(SEQ_NUMBER_SIZE, "big")
        + filename.encode()
    )

    n_tries = 0
    while n_tries < MAX_TRIES:
        n_tries += 1
        try:
            udp_socket.sendto(initial_packet, address_to_connect)
            response_from_server, server_address = udp_socket.recvfrom(PACKET_SIZE)
            response_type, _ = get_header(response_from_server)

            # Si el servidor devuelve ERROR en cualquier caso imprimimos el mismo
            if response_type == Type.ERROR:
                error_msg = get_payload(response_from_server).decode()
                print(f"ERROR: {error_msg}")
                return response_type, server_address

            # Si el servidor devuelve ACK y estamos en UPLOAD, significa que esta todo bien
            if connection_type == Type.UPLOAD and response_type == Type.ACK:
                return response_type, server_address

            # Si el servidor devuelve DATA y estamos en DOWNLOAD, significa que esta todo bien
            if connection_type == Type.DOWNLOAD and response_type == Type.DATA:
                return response_type, server_address

            raise TimeoutError
        except timeout:
            continue

    print(f"ERROR: Failed to establish connection with the server")
    return Type.ERROR, "server_address"


def receive_connection(packet_to_send, udp_socket, address_to_connect, type_to_expect):
    n_tries = 0
    while n_tries < MAX_TRIES:
        n_tries += 1
        try:
            # El packet que enviamos va a ser de tipo ACK/ERROR
            udp_socket.sendto(packet_to_send, address_to_connect)
            response_from_server, _ = udp_socket.recvfrom(PACKET_SIZE)
            response_type, _ = get_header(response_from_server)

            # El paquete que vamos a esperar va a ser ACK/DATA dependiendo del caso
            if response_type == type_to_expect:
                return response_type

            raise TimeoutError
        except timeout:
            continue

    print(f"ERROR: Failed to establish connection with the server")
    return Type.ERROR
