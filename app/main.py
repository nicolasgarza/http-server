import socket
import threading
import sys
import os.path

HTTP_400_BAD_REQUEST = "HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\nContent-Length: 11\r\n\r\nBad Request"
HTTP_404_NOT_FOUND = "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nContent-Length: 9\r\n\r\nNot Found"
VALID_ENCODINGS = {"gzip"}

print("System args:")
print(sys.argv)
file_dir = sys.argv[-1]


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    while True:
        conn, _ = server_socket.accept()

        data = conn.recv(1024).decode()
        print("recieved: " + repr(data))

        thread = threading.Thread(target=route_req, args=(conn, data))
        thread.start()


def route_req(conn, raw_data):
    print("parsed data:")
    parsed_data = raw_data.split(" ")
    print(parsed_data)
    if parsed_data[1] == "/":
        conn.sendall(
            build_http_req("200", "OK", "OK", {"Content-Type": "text/plain"}).encode()
        )

    elif parsed_data[1].startswith("/echo"):
        if raw_data.find("Accept-Encoding") == -1:
            conn.sendall(handle_echo(parsed_data[1]).encode())
        else:
            conn.sendall(handle_compressed_echo(raw_data).encode())

    elif parsed_data[1].startswith("/user-agent"):
        conn.sendall(handle_user_agent(parsed_data).encode())

    elif parsed_data[0] == "GET":
        conn.sendall(handle_get_file(parsed_data[1]).encode())

    elif parsed_data[0] == "POST":
        conn.sendall(handle_post_file(raw_data).encode())
    else:
        conn.sendall(HTTP_404_NOT_FOUND.encode())


def handle_echo(parsed_data):
    parsed = parsed_data.split("/")
    print("parsed data for echo: ")
    print(parsed)
    return build_http_req("200", "OK", parsed[2], {"Content-Type": "text/plain"})


def handle_user_agent(parsed_data):
    parsed = parsed_data[-1].rstrip("\r\n")
    return build_http_req("200", "OK", parsed, {"Content-Type": "text/plain"})


def handle_get_file(file_path):
    global file_dir
    path = f"{file_dir}{file_path[len('/files'):]}"
    print("target file path:", path)
    if not os.path.isfile(path):
        print("file does not exist")
        return HTTP_404_NOT_FOUND

    target_file = open(path, "r")
    text = target_file.read()
    return build_http_req(
        "200", "OK", text, {"Content-Type": "application/octet-stream"}
    )


def handle_post_file(parsed_data):
    global file_dir
    path = os.path.join(file_dir, parsed_data.split(" ")[1].lstrip("/files"))
    print("target file path", path)
    print("data to work with: " + repr(parsed_data))

    write_data = parsed_data.split("\r\n")[-1]
    print("write data:", write_data)

    f = open(path, "a")
    f.write(write_data)
    f.close()
    return build_http_req("201", "Created", "Created", {"Content-Type": "text/plain"})


def handle_compressed_echo(parsed_data):
    lines = parsed_data.split("\r\n")
    print(lines)
    accept_encoding = None
    for line in lines:
        if line.startswith("Accept-Encoding:"):
            accept_encoding = line.split(":", 1)[1].strip()
            print(accept_encoding)
            break
    headers = {"Content-Type": "text/plain"}
    if accept_encoding and accept_encoding in VALID_ENCODINGS:
        headers["Content-Encoding"] = accept_encoding

    return build_http_req("200", "OK", "foo", headers=headers)


def build_http_req(code, reason, msg, headers=None):
    if headers is None:
        headers = {}
    optional_headers = "\r\n".join(f"{key}: {value}" for key, value in headers.items())
    return f"HTTP/1.1 {code} {reason}\r\n{optional_headers}\r\nContent-Length: {len(msg)}\r\n\r\n{msg}"


if __name__ == "__main__":
    main()
