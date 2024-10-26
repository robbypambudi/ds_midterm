import os
import sys

import zmq


class RETURN_VALUE:
    ERR_STRING = "ERROR"
    SUCCESS_STRING = "SUCCESS"

    ERR_BYTES = ERR_STRING.encode()
    SUCCESS_BYTES = SUCCESS_STRING.encode()


class Server:
    SHARED_DIR = os.getcwd() + os.sep + "shared2"

    def __init__(self, machine_name: str, endpoint: str) -> None:
        self.__machine_name = machine_name
        self.__endpoint = endpoint
        self.__context = zmq.Context()
        self.__server = self.__context.socket(zmq.REP)

        self.__server.bind(endpoint)

    def destroy(self) -> None:
        self.__server.setsockopt(zmq.LINGER, 0)
        self.__server.close()
        self.__context.term()

        return

    def list_all_files(self, include_hidden=False) -> list[bytes]:
        all_files: list[bytes] = []

        for _, _, files in os.walk(self.SHARED_DIR):
            for file in files:
                # check if file starts with dot (hidden)
                if file.startswith(".") and not include_hidden:
                    continue

                all_files.append(file.encode())

        return all_files

    def start(self) -> None:
        print(f"I: Starting server at {self.__endpoint}")

        while True:
            msg = self.__server.recv_multipart()
            if not msg:
                break

            print(f"I: Received message: {msg}")

            sequence = msg[1].decode()
            command = msg[2].decode()

            if command == "HEALTH":
                self.__server.send_multipart(
                    [
                        self.__machine_name.encode(),
                        sequence.encode(),
                        RETURN_VALUE.SUCCESS_BYTES,
                        b"OK",
                    ]
                )
            elif command == "LIST":
                files = self.list_all_files()
                self.__server.send_multipart(
                    [
                        self.__machine_name.encode(),
                        sequence.encode(),
                        RETURN_VALUE.SUCCESS_BYTES,
                    ]
                    + files
                )
            elif command == "LIST_ALL":
                files = self.list_all_files(include_hidden=True)
                self.__server.send_multipart(
                    [
                        self.__machine_name.encode(),
                        sequence.encode(),
                        RETURN_VALUE.SUCCESS_BYTES,
                    ]
                    + files
                )
            elif command == "DOWNLOAD":
                if len(msg) != 5:
                    self.__server.send_multipart(
                        [
                            self.__machine_name.encode(),
                            sequence.encode(),
                            RETURN_VALUE.ERR_BYTES,
                            b"DOWNLOAD <machine_name> <filename>",
                        ]
                    )
                    continue

                if msg[3].decode() != self.__machine_name:
                    self.__server.send_multipart(
                        [
                            self.__machine_name.encode(),
                            sequence.encode(),
                            RETURN_VALUE.ERR_BYTES,
                            b"Not this one",
                        ]
                    )
                    continue

                filename = msg[4].decode()

                if not os.path.exists(self.SHARED_DIR + os.sep + filename):
                    self.__server.send_multipart(
                        [
                            self.__machine_name.encode(),
                            sequence.encode(),
                            RETURN_VALUE.ERR_BYTES,
                            b"File not found",
                        ]
                    )
                    continue

                msg = [
                    self.__machine_name.encode(),
                    sequence.encode(),
                    RETURN_VALUE.SUCCESS_BYTES,
                ]

                with open(self.SHARED_DIR + os.sep + filename, "rb") as f:
                    data = f.read(1024)
                    if data:
                        while data:
                            msg += [data]
                            data = f.read(1024)

                    self.__server.send_multipart(msg)
            else:
                self.__server.send_multipart(
                    [
                        self.__machine_name.encode(),
                        sequence.encode(),
                        RETURN_VALUE.ERR_BYTES,
                        b"Invalid command",
                    ]
                )

        self.destroy()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("I: Syntax: %s <machine_name> <endpoint>" % sys.argv[0])
        sys.exit(0)

    server = Server(sys.argv[1], sys.argv[2])
    server.start()
