import socket
import threading
import sys
import os.path

HTTP_400_BAD_REQUEST = "HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\nContent-Length: 11\r\n\r\nBad Request"
HTTP_404_NOT_FOUND = "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nContent-Length: 9\r\n\r\nNot Found"

file_dir = sys.argv[-1]


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
        conn.sendall(build_http_req("text/plain", "OK").encode())
    elif parsed_data[1].startswith("/echo"):
        conn.sendall(handle_echo(parsed_data[1]).encode())
    elif parsed_data[1].startswith("/user-agent"):
        conn.sendall(handle_user_agent(parsed_data).encode())
    elif parsed_data[0] == "GET":
        conn.sendall(handle_get_file(parsed_data[1]).encode())
    else:
        conn.sendall(HTTP_404_NOT_FOUND.encode())


def handle_echo(parsed_data):
    parsed = parsed_data.split("/")
    return build_http_req("text/plain", parsed[2])


def handle_user_agent(parsed_data):
    parsed = parsed_data[-1].rstrip("\r\n")
    return build_http_req("text/plain", parsed)


def handle_get_file(file_path):
    global file_dir
    path = f"{file_dir}{file_path.lstrip("/files")}"
    print("target file path:", path)
    if not os.path.isfile(path):
        print("file does not exist")
        return HTTP_404_NOT_FOUND

    target_file = open(path, "r")
    text = "\n".join(target_file.readlines())
    return build_http_req("application/octet-stream", text)


def build_http_req(content_type, msg):
    return f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nContent-Length: {len(msg)}\r\n\r\n{msg}"


if __name__ == "__main__":
    main()
