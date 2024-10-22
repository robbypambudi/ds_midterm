import os
import sys

import zmq


class Server:
    SHARE_DIR = os.getcwd() + os.sep + "shared"

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

    def start(self) -> None:
        print(f"I: Starting server at {self.__endpoint}")

        while True:
            msg = self.__server.recv_multipart()

            if not msg:
                break

            assert len(msg) == 2

            address = msg[0]
            reply = [address, b"OK"]
            self.__server.send_multipart(reply)

        self.destroy()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("I: Syntax: %s <endpoint>" % sys.argv[0])
        sys.exit(0)

    server = Server("mesin_1", sys.argv[1])
    server.start()
