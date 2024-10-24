import os
import sys
from random import randint

import zmq


class RETURN_VALUE:
    ERR_STRING = "ERROR"
    SUCCESS_STRING = "SUCCESS"

    ERR_BYTES = ERR_STRING.encode()
    SUCCESS_BYTES = SUCCESS_STRING.encode()


class Client:
    MAX_RETRIES = 3
    MAX_REQUESTS_TIMEOUT = 3000

    def __init__(self, server_list: list[str]) -> None:
        self.__server_list = server_list

        # define the variable data type only
        self.__context = zmq.Context()
        self.__client: zmq.SyncSocket
        self.__poller = zmq.Poller()
        self.__sockets = dict()

        self.client_id = "%04X-%04X" % (randint(0, 0x10000), randint(0, 0x10000))

    def destroy(self):
        self.__client.setsockopt(zmq.LINGER, 0)  # Terminate early
        self.__client.close()
        self.__context.term()

    def send_request(self, *request):
        reply = list()

        for endpoint in self.__server_list:
            server_reply: list[bytes] = []

            for _ in range(client.MAX_RETRIES):
                print("%s: Connecting to %s" % (self.client_id, endpoint))
                self.__client = self.__context.socket(zmq.REQ)
                self.__client.connect(endpoint)

                msg = [self.client_id.encode()] + list(request)
                self.__client.send_multipart(msg)

                self.__poller.register(self.__client, zmq.POLLIN)
                self.__sockets.update(self.__poller.poll(self.MAX_REQUESTS_TIMEOUT))

                if self.__sockets.get(self.__client) == zmq.POLLIN:
                    server_reply = self.__client.recv_multipart()

                if server_reply:
                    reply.append(server_reply)
                    self.__poller.unregister(self.__client)
                    break

            if server_reply == []:
                print(f"E: Server {endpoint} seems to be offline")

        return reply


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(f"E: Syntax: {sys.argv[0]} <server_endpoint>...")
        sys.exit(1)

    client = Client(sys.argv[1:])
    print(f"I: Client started: ID: {client.client_id}")

    while True:
        # List Command
        print("List of commands: ")
        print("- HEALTH")
        print("- LIST")
        print("- LIST_ALL")
        print("- DOWNLOAD <filename>")
        print("- EXIT")
        command = input("Enter your command: ")

        try:
            if command == "EXIT":
                print("I: Exiting program...")
                client.destroy()
                os._exit(os.EX_OK)
            elif command == "HEALTH":
                res = client.send_request(command.encode())
                for reply in res:
                    print(f"M: server {reply[0].decode()} status: {reply[1].decode()}")
                    print(f"M: reply: {reply[2].decode()}")
            elif command == "LIST" or command == "LIST_ALL":
                res = client.send_request(command.encode())
                for reply in res:
                    print(f"M: server {reply[0].decode()} status: {reply[1].decode()}")
                    for filename in reply[2:]:
                        print(f"M: Files: {filename.decode()}")
            elif command.startswith("DOWNLOAD"):
                command = command.split(" ")
                
                if len(command) != 3:
                    print("E: DOWNLOAD <machine_name> <filename>")
                    continue

                res = client.send_request(
                    command[0].encode(), command[1].encode(), command[2].encode()
                )

                if res[1] == RETURN_VALUE.ERR_BYTES:
                    print(f"E: Cannot download the file: {res[2].decode()}")
                else:
                    with open(f"client_{command[1]}_{command[2]}", "wb") as f:
                        f.write(res[0][0])

            else:
                print("E: Invalid command")

        except Exception as e:
            print(f"E: {e}")
            client.destroy()
            sys.exit(1)
