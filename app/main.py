import socket
import threading
import sys
import logging
import os.path

HTTP_400_BAD_REQUEST = "HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\nContent-Length: 11\r\n\r\nBad Request"
HTTP_404_NOT_FOUND = "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nContent-Length: 9\r\n\r\nNot Found"
VALID_ENCODINGS = {"gzip"}

logging.basicConfig(level=logging.DEBUG)


class HTTPRequestHandler:
    def __init__(self, file_dir):
        self.file_dir = file_dir

    def handle_request(self, conn, raw_data):
        logging.debug(f"Received data: {repr(raw_data)}")
        parsed_data = raw_data.split(" ")

        if len(parsed_data) < 2:
            conn.sendall(HTTP_400_BAD_REQUEST.encode())
            return

        method, path = parsed_data[0], parsed_data[1]

        if path == "/":
            conn.sendall(
                self.build_http_req(
                    "200", "OK", "OK", {"Content-Type": "text/plain"}
                ).encode()
            )

        elif path.startswith("/echo"):
            if "Accept-Encoding" not in raw_data:
                conn.sendall(self.handle_echo(path).encode())
            else:
                conn.sendall(self.handle_compressed_echo(raw_data).encode())

        elif path.startswith("/user-agent"):
            conn.sendall(self.handle_user_agent(parsed_data).encode())

        elif method == "GET":
            conn.sendall(self.handle_get_file(path).encode())

        elif method == "POST":
            conn.sendall(self.handle_post_file(raw_data).encode())
        else:
            conn.sendall(HTTP_404_NOT_FOUND.encode())

    def handle_echo(self, path):
        parsed = path.split("/")
        logging.debug(f"Parsed data for echo: {parsed}")
        return self.build_http_req(
            "200", "OK", parsed[2], {"Content-Type": "text/plain"}
        )

    def handle_user_agent(self, parsed_data):
        user_agent = parsed_data[-1].rstrip("\r\n")
        return self.build_http_req(
            "200", "OK", user_agent, {"Content-Type": "text/plain"}
        )

    def handle_get_file(self, file_path):
        if file_path.startswith("/"):
            file_path = file_path[1:]

        if file_path.startswith("files"):
            path = os.path.join(self.file_dir, file_path[len("files/") :])
        else:
            path = os.path.join(self.file_dir, file_path)

        logging.debug(f"Target file path: {path}")
        if not os.path.isfile(path):
            logging.error("File does not exist")
            return HTTP_404_NOT_FOUND

        with open(path, "r") as target_file:
            text = target_file.read()
        return self.build_http_req(
            "200", "OK", text, {"Content-Type": "application/octet-stream"}
        )

    def handle_post_file(self, raw_data):
        relative_path = raw_data.split(" ")[1]
        if relative_path.startswith("/"):
            relative_path = relative_path[1:]
        path = os.path.join(self.file_dir, relative_path[len("files/") :])
        logging.debug(f"Target file path: {path}")
        logging.debug(f"Data to work with: {repr(raw_data)}")

        write_data = raw_data.split("\r\n")[-1]
        logging.debug(f"Write data: {write_data}")

        with open(path, "a") as f:
            f.write(write_data)
        return self.build_http_req(
            "201", "Created", "Created", {"Content-Type": "text/plain"}
        )

    def handle_compressed_echo(self, raw_data):
        lines = raw_data.split("\r\n")
        logging.debug(f"Lines: {lines}")
        accept_encoding, encodings = None, []
        for line in lines:
            if line.lower().startswith("accept-encoding:"):
                accept_encoding = line.split(":", 1)[1].strip()
                encodings = [enc.strip() for enc in accept_encoding.split(",")]
                logging.debug(f"Accept-Encodings: {accept_encoding}")
                break

        headers = {"Content-Type": "text/plain"}
        for encoding in encodings:
            if encoding and encoding.strip() in VALID_ENCODINGS:
                headers["Content-Encoding"] = encoding
                break

        return self.build_http_req("200", "OK", "foo", headers=headers)

    def build_http_req(self, code, reason, msg, headers=None):
        if headers is None:
            headers = {}
        optional_headers = "\r\n".join(
            f"{key}: {value}" for key, value in headers.items()
        )
        return f"HTTP/1.1 {code} {reason}\r\n{optional_headers}\r\nContent-Length: {len(msg)}\r\n\r\n{msg}"


def main():
    logging.info("Logs from your program will appear here!")

    sys_args = sys.argv
    file_dir = sys_args[-1]
    logging.debug(f"Root file directory: {file_dir}")

    handler = HTTPRequestHandler(file_dir)

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    while True:
        conn, _ = server_socket.accept()

        data = conn.recv(1024).decode()
        logging.debug(f"Received: {repr(data)}")

        thread = threading.Thread(target=handler.handle_request, args=(conn, data))
        thread.start()


if __name__ == "__main__":
    main()
