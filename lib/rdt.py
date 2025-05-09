from enum import Enum
from socket import *
import time
import random

random.seed()


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


def print_verbose(msg, verbose):
    if verbose:
        print(msg)


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


def send_data(seq_number, socket, address, data):
    print(f"Sent packet #{seq_number}")
    data_packet = (
        Type.DATA.value.to_bytes(TYPE_SIZE, "big")
        + seq_number.to_bytes(SEQ_NUMBER_SIZE, "big")
        + data
    )
    socket.sendto(data_packet, address)


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


def recv_file_sw(udp_socket, filepath):
    response_type = Type.ACK
    packet_counter = 0
    file = open(filepath, "ab")

    # Mientras el tipo no sea CLOSE
    while response_type != Type.CLOSE:
        # Leo del socket:
        try:
            response_from_server, server_address = udp_socket.recvfrom(PACKET_SIZE)
            response_type, response_seq_number = get_header(response_from_server)

            # Si lo que llego es tipo DATA y su secuencia es igual a counter:
            if received_expected_data(
                response_type, response_seq_number, packet_counter + 1
            ):
                # Es el que esperabamos y lo escribimos a archivo, mandamos ACK de su numero de secuencia y aumentamos counter
                payload = get_payload(response_from_server)
                file.write(payload)
                file.flush()
                send_ack(response_seq_number, udp_socket, server_address)
                packet_counter += 1
            else:
                # Reenviamos ACK
                send_ack(packet_counter, udp_socket, server_address)
        except timeout:
            continue

    print(f"Received CLOSE packet")
    file.close()


def send_file_sw(udp_socket, filepath, receiver_address):
    packet_counter = 1
    file = open(filepath, "rb")
    data_read = file.read(PAYLOAD_SIZE)

    # Mientras el tipo no sea CLOSE
    while data_read:
        send_data(packet_counter, udp_socket, receiver_address, data_read)

        # Leo del socket:
        try:
            response_type, response_seq_number = receive_ack(udp_socket)

            # Si lo que llego es tipo ACK es ACK que esperabamos, enviamos el siguiente:
            if received_expected_ack(
                response_type, response_seq_number, packet_counter
            ):
                data_read = file.read(PAYLOAD_SIZE)
                packet_counter += 1

        except timeout:
            print(
                f"Wait for ACK #{packet_counter} timed out, resending previous packet #{packet_counter}"
            )

    send_close(packet_counter, udp_socket, receiver_address)
    file.close()


def received_ack_is_within_window(received_type, received_seq_number, base):
    if received_type == Type.ACK:
        if base <= received_seq_number < base + WINDOW_SIZE:
            return True
    return False


def advance_windows(acked_window: list[bool], buffer_window, timer_window):
    pos = 0
    print("Advancing buffered packets window...")

    while len(acked_window) > 0 and acked_window[0] == True:
        acked_window.pop(0)
        buffer_window.pop(0)
        timer_window.pop(0)
        pos += 1

    acked_window.extend([False] * pos)

    return pos


def check_for_timeouts_and_resend(
    acked_window, buffer_window, timer_window, socket, address
):
    print(f"Checking for timeouts for sent packets...")

    pos = 0
    for acked in acked_window:
        if len(buffer_window) > pos and len(timer_window) > pos:
            if acked == False and timer_window[pos] < time.time():
                timer_window[pos] = time.time() + SENDER_TIMEOUT_SR
                send_data(
                    buffer_window[pos][0],
                    socket,
                    address,
                    buffer_window[pos][1],
                )
            pos += 1


def send_file_sr(udp_socket, filepath, receiver_address):
    base = 0
    packet_counter = 0
    acked_window = [False] * WINDOW_SIZE
    buffer_window = []
    timer_window = []

    file = open(filepath, "rb")
    data_read = file.read(PAYLOAD_SIZE)

    while (
        data_read or len(buffer_window) > 0
    ):  # Falta ver bien esta condicion para el caso en que leimos todo el archivo y queden aun unACKed en la window
        if packet_counter < base + WINDOW_SIZE and data_read:
            # packet gets sent
            send_data(packet_counter, udp_socket, receiver_address, data_read)
            # guardo data en buffer window
            # guardo timer en timer_window
            buffer_window.append((packet_counter, data_read))
            timer_window.append(time.time() + SENDER_TIMEOUT_SR)
            packet_counter += 1
            data_read = file.read(PAYLOAD_SIZE)
        else:
            try:
                # Leo del socket:
                response_type, response_seq_number = receive_ack(udp_socket)

                # Si lo que llego es tipo ACK y es ACK que esperabamos, enviamos el siguiente:
                if received_ack_is_within_window(
                    response_type, response_seq_number, base
                ):
                    print(f"Received expected ACK #{response_seq_number}")
                    acked_window[response_seq_number - base] = True

                    # si era el unACKED mas chico
                    if response_seq_number == base:
                        # se avanza la window hasta el siguiente unACKED mas chico
                        base += advance_windows(
                            acked_window, buffer_window, timer_window
                        )

            except timeout:
                # check timers and resend packets if needed
                check_for_timeouts_and_resend(
                    acked_window,
                    buffer_window,
                    timer_window,
                    udp_socket,
                    receiver_address,
                )

    send_close(packet_counter, udp_socket, receiver_address)
    file.close()


def advance_recved_window(recved_window: list[bool], buffer_window, file):
    pos = 0
    print("Avancing buffered packets received window...")

    while len(recved_window) > 0 and recved_window[0] == True:
        recved_window.pop(0)
        buffered_data = buffer_window.pop(0)
        print(f"Writing to file buffered packet #{buffered_data[0]}")
        file.write(buffered_data[1])
        file.flush()
        pos += 1

    recved_window.extend([False] * pos)
    buffer_window.extend([(0, (0).to_bytes(1, "big"))] * pos)

    return pos


def recv_file_sr(udp_socket, filepath):
    response_type = Type.ACK
    base = 0
    recved_window = [False] * WINDOW_SIZE
    buffer_window = [(0, (0).to_bytes(1, "big"))] * WINDOW_SIZE
    file = open(filepath, "ab")

    # Mientras el tipo no sea CLOSE
    while response_type != Type.CLOSE:
        try:
            # Leo del socket:
            response_from_server, server_address = udp_socket.recvfrom(PACKET_SIZE)
            response_type, response_seq_number = get_header(response_from_server)
        except timeout:
            continue

        if response_type != Type.DATA:
            print(f"Received unexpected non DATA packet")
            continue

        # If a packet n is received and its within the window:
        if base <= response_seq_number < base + WINDOW_SIZE:
            send_ack(response_seq_number, udp_socket, server_address)
            if response_seq_number == base:
                # Es el que esperabamos y lo escribimos a archivo, mandamos ACK de su numero de secuencia y aumentamos counter
                print(f"Received packet #{response_seq_number} in-order")
                recved_window[0] = True
                payload = get_payload(response_from_server)
                buffer_window[response_seq_number - base] = (
                    response_seq_number,
                    payload,
                )

                base += advance_recved_window(recved_window, buffer_window, file)
            else:
                print(f"Received packet #{response_seq_number} out-of-order")
                recved_window[response_seq_number - base] = True
                payload = get_payload(response_from_server)
                buffer_window[response_seq_number - base] = (
                    response_seq_number,
                    payload,
                )
            print(f"Sent ACK #{response_seq_number}")
        elif response_seq_number < base:
            # Reenviamos ACK del paquete que llego
            print(f"Received packet #{response_seq_number} left-of-window")
            send_ack(response_seq_number, udp_socket, server_address)

    print(f"Received CLOSE packet")
    file.close()
