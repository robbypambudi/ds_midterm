import os
import sys

import zmq


class Server:
    SHARED_DIR = os.getcwd() + os.sep + "shared"

    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint
        self.context = zmq.Context()
        self.server = self.context.socket(zmq.REP)

        self.server.bind(endpoint)

    def destroy(self) -> None:
        self.server.setsockopt(zmq.LINGER, 0)
        self.server.close()
        self.context.term()

    def list_all_files(self, include_hidden=False) -> list[bytes]:
        all_files: list[bytes] = []

        for _, _, files in os.walk(self.SHARED_DIR):
            for file in files:
                # check if file starts with dot (hidden)
                if file.startswith(".") and not include_hidden:
                    continue

                all_files.append(file.encode())

        return all_files

    def start_server(self) -> None:
        print(f"I: Starting server at {self.endpoint}")

        while True:
            msg = self.server.recv_multipart()

            if not msg:
                break

            print(f"I: Received message: {msg}")

            match msg[0].decode():
                case "check":
                    self.server.send(b"OK")
                # list files without hidden files
                case "list":
                    files = self.list_all_files()
                    self.server.send_multipart(files)
                # list files with hidden files
                case "list_all":
                    files = self.list_all_files(include_hidden=True)
                    self.server.send_multipart(files)
                case "get":
                    # check if the filename is provided
                    if not msg[1]:
                        self.server.send(b"Filename not provided")

                    filename = msg[1].decode()
                    if not os.path.exists(self.SHARED_DIR + os.sep + filename):
                        self.server.send(b"File not found")

                    self.server.send(b"File found")
                case _:
                    self.server.send(b"Invalid command")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"I: Syntax: {sys.argv[0]} <endpoint>")
        sys.exit(0)

    server = Server(sys.argv[1])
    server.start_server()
