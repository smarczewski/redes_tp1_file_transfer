from lib.rdt_shared import *
import time


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
