import socket


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    conn, _ = server_socket.accept()

    data = conn.recv(1024).decode()
    print("recieved: " + data)

    parsed = data.split(" ")[1]
    print("parsed: " + parsed)

    if parsed == "/":
        conn.sendall("HTTP/1.1 200 OK\r\n\r\n".encode())
    else:
        conn.sendall("HTTP/1.1 404 Not Found\r\n\r\n".encode())


if __name__ == "__main__":
    main()
