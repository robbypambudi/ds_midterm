import os
import sys

import zmq


class Server:
    SHARED_DIR = os.getcwd() + os.sep + "shared"

    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint
        self.server = zmq.Context().socket(zmq.REP)

        self.server.bind(endpoint)

        # sock options
        self.server.setsockopt(zmq.LINGER, 0)

    def list_all_files(self, include_hidden=False):
        all_files: list[str] = []

        for _, _, files in os.walk(self.SHARED_DIR):
            for file in files:
                # check if file starts with dot (hidden)
                if file.startswith(".") and not include_hidden:
                    continue

                all_files.append(file)

        return all_files

    def start_server(self) -> None:
        print(f"I: Starting server at {self.endpoint}")

        while True:
            msg = self.server.recv_multipart()

            if not msg:
                break

            print(f"I: Received message: {msg}")
            self.server.send_multipart(msg)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"I: Syntax: {sys.argv[0]} <endpoint>")
        sys.exit(0)

    server = Server(sys.argv[1])
    server.start_server()
