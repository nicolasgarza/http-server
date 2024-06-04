import socket
import threading

HTTP_400_BAD_REQUEST = "HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\nContent-Length: 11\r\n\r\nBad Request"
HTTP_404_NOT_FOUND = "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nContent-Length: 9\r\n\r\nNot Found"


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    while True:
        conn, _ = server_socket.accept()

        data = conn.recv(1024).decode()
        print("recieved: " + data)

        thread = threading.Thread(target=route_req, args=(conn, data))
        thread.start()


def route_req(conn, parsed_data):
    parsed_data = parsed_data.split(" ")
    print("parsed data:")
    print(parsed_data)
    if parsed_data[1] == "/":
        conn.sendall(build_http_req("OK").encode())
    elif parsed_data[1].startswith("/echo"):
        conn.sendall(handle_echo(parsed_data[1]).encode())
    elif parsed_data[1].startswith("/user-agent"):
        conn.sendall(handle_user_agent(parsed_data).encode())
    else:
        conn.sendall(HTTP_404_NOT_FOUND.encode())


def handle_echo(parsed_data):
    parsed = parsed_data.split("/")
    return build_http_req(parsed[2])


def handle_user_agent(parsed_data):
    parsed = parsed_data[-1].rstrip("\r\n")
    return build_http_req(parsed)


def build_http_req(msg):
    return f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(msg)}\r\n\r\n{msg}"


if __name__ == "__main__":
    main()
