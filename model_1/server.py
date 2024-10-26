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
        self.machine_name = machine_name
        self.__endpoint = endpoint
        self.__context = zmq.Context()
        self.__server = self.__context.socket(zmq.REP)

        # bind the server
        self.__server.bind(endpoint)

    def destroy(self) -> None:
        # destroy server
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

    def start_server(self) -> None:
        print(f"I: Starting server at {self.__endpoint}")

        while True:
            msg = self.__server.recv_multipart()

            if not msg:
                break

            print(f"I: Received message: {msg}")

            client_id = msg[0].decode()
            command = msg[1].decode()

            if command == "HEALTH":
                print(f"I: Sending reply to {client_id}")
                self.__server.send_multipart(
                    [self.machine_name.encode(), RETURN_VALUE.SUCCESS_BYTES, b"OK"]
                )
            elif command == "LIST":
                files = self.list_all_files()

                print(f"I: Sending reply to {client_id}")
                self.__server.send_multipart(
                    [self.machine_name.encode(), RETURN_VALUE.SUCCESS_BYTES] + files
                )
            elif command == "LIST_ALL":
                files = self.list_all_files(include_hidden=True)

                print(f"I: Sending reply to {client_id}")
                self.__server.send_multipart(
                    [self.machine_name.encode(), RETURN_VALUE.SUCCESS_BYTES] + files
                )
                
            elif command == "DOWNLOAD":
                machine = msg[2].decode()
                filename = msg[3].decode()

                msg = [self.machine_name.encode()]

                if self.machine_name != machine:
                    self.__server.send_multipart(
                        [
                            self.machine_name.encode(),
                            RETURN_VALUE.ERR_BYTES,
                            b"Not this one",
                        ]
                    )
                    continue

                # check if file exists
                if not os.path.exists(self.SHARED_DIR + os.sep + filename):
                    self.__server.send_multipart(
                        [
                            self.machine_name.encode(),
                            RETURN_VALUE.ERR_BYTES,
                            b"File not found",
                        ]
                    )
                    continue

                print(f"I: Sending reply to {client_id}")

                # send the file
                with open(self.SHARED_DIR + os.sep + filename, "rb") as f:
                    data = f.read(1024)
                    if data:
                        msg += [RETURN_VALUE.SUCCESS_BYTES]

                        while data:
                            msg += [data]
                            data = f.read(1024)

                        self.__server.send_multipart(msg)
                    else:
                        self.__server.send_multipart(msg + [RETURN_VALUE.SUCCESS_BYTES])

            else:
                print(f"E: Invalid command, sending reply to {client_id}")
                self.__server.send_multipart(
                    [
                        self.machine_name.encode(),
                        RETURN_VALUE.ERR_BYTES,
                        b"Invalid command",
                    ]
                )

        self.destroy()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"I: Syntax: {sys.argv[0]} <machine_name> <endpoint>")
        sys.exit(0)

    server = Server(sys.argv[1], sys.argv[2])
    server.start_server()
