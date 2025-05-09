from lib.rdt_shared import *


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
