import sys
from random import randint
from tabulate import tabulate

import zmq
import time

def loading_animation():
    for _ in range(3):  # Ulangi beberapa kali
        for dot in [".  ", ".. ", "..."]:
            sys.stdout.write(f"\rLoading{dot}")
            sys.stdout.flush()
            time.sleep(0.2)

class RETURN_VALUE:
    ERR_STRING = "ERROR"
    SUCCESS_STRING = "SUCCESS"

    ERR_BYTES = ERR_STRING.encode()
    SUCCESS_BYTES = SUCCESS_STRING.encode()


class Client:
    MAX_RETRIES = 3
    MAX_REQUESTS_TIMEOUT = 3000

    def __init__(self, server_list: list[str]) -> None:
        self.server_list = server_list

        # client identifier
        self.client_id = "%04X-%04X" % (randint(0, 0x10000), randint(0, 0x10000))

        # socket configuration
        self.__context = zmq.Context()

    def destroy(self, client: zmq.Socket) -> None:
        client.setsockopt(zmq.LINGER, 0)
        client.close()
        return

    def exit(self) -> None:
        self.__context.term()
        return

    def send_request(self, endpoint, request: list):
        client_socket = self.__context.socket(zmq.REQ)
        client_socket.connect(endpoint)

        msg = [self.client_id.encode()] + request
        client_socket.send_multipart(msg)

        poll = zmq.Poller()
        poll.register(client_socket, zmq.POLLIN)

        socks = dict(poll.poll(self.MAX_REQUESTS_TIMEOUT))
        if socks.get(client_socket) == zmq.POLLIN:
            reply = client_socket.recv_multipart()
        else:
            reply = None

        self.destroy(client_socket)

        return reply


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(f"E: Syntax: {sys.argv[0]} <server_endpoint>...")
        sys.exit(1)

    client = Client(sys.argv[1:])
    print(f"I: Client started: ID: {client.client_id}")

    while True:
        all_replies: list = []

        # List Command
        print("List of commands: ")
        print("- HEALTH")
        print("- LIST")
        print("- LIST_ALL")
        print("- DOWNLOAD <filename>")
        print("- EXIT")
        command = input("Enter your command: ").split(" ")
        bytes_command: list[bytes] = []
        for i in range(0, len(command)):
            bytes_command.append(command[i].encode())

        try:
            if command[0] == "EXIT":
                print("I: Exiting program...")
                client.exit()
                sys.exit(0)
            elif command[0] == "HEALTH":
                for server in client.server_list:
                    for retry in range(client.MAX_RETRIES):
                        server_reply = client.send_request(server, bytes_command)
                        print(f"Server: {server}")

                        if server_reply:
                            print(f"Reply: {f'{server_reply[2].decode()}'}")
                            break
                        else :
                            print(f"Server {server} is not available")
                            print("Trying reconnecting...")
                print("")
                    
            elif command[0] == "LIST":
                # Inisialisasi daftar data di luar loop server
                all_data = []

                for server in client.server_list:
                    headers = ["MESIN", "FILES"]
                    data = []

                    for retry in range(client.MAX_RETRIES):
                        server_reply = client.send_request(server, bytes_command)

                        if server_reply:
                            # Ambil nama mesin
                            mesin_name = server_reply[0].decode()

                            # Ambil daftar file dari reply dan tambahkan ke data
                            for i in range(2, len(server_reply)):
                                file_name = server_reply[i].decode()
                                data.append([mesin_name, file_name])

                            break
                        else:
                            print(f"Server {server} is not available")
                            print("Trying reconnecting...")

                    # Jika data tidak kosong, tambahkan ke all_data dan tampilkan tabel
                    if data:
                        all_data.extend(data)
                        print("Server: ", server)
                        print(tabulate(data, headers, tablefmt="grid"))
                        print("")

            elif command[0] == "LIST_ALL":
                # Inisialisasi daftar data di luar loop server
                all_data = []

                for server in client.server_list:
                    headers = ["MESIN", "FILES"]
                    data = []

                    for retry in range(client.MAX_RETRIES):
                        server_reply = client.send_request(server, bytes_command)

                        if server_reply:
                            # Ambil nama mesin
                            mesin_name = server_reply[0].decode()

                            # Ambil daftar file dari reply dan tambahkan ke data
                            for i in range(2, len(server_reply)):
                                file_name = server_reply[i].decode()
                                data.append([mesin_name, file_name])

                            break
                        else:
                            print(f"Server {server} is not available")
                            print("Trying reconnecting...")

                    # Jika data tidak kosong, tambahkan ke all_data dan tampilkan tabel
                    if data:
                        all_data.extend(data)
                        print("Server: ", server)
                        print(tabulate(data, headers, tablefmt="grid"))
                        print("")

            elif command[0] == "DOWNLOAD":
                for server in client.server_list:
                    for retry in range(client.MAX_RETRIES):
                        server_reply = client.send_request(server, bytes_command)

                        if server_reply:
                            all_replies.append(server_reply)
                            break
                print("Downloading file...")                
                failedFlag = 0
                for reply in all_replies:
                    if (
                        len(reply) == 3
                        and reply[1] == b"ERROR"
                        and reply[2] == b"Not this one"
                    ):
                        failedFlag += 1
                        continue
                    # elif File not found
                    elif (
                        len(reply) == 3
                        and reply[1] == b"ERROR"
                        and reply[2] == b"File not found"
                    ):
                        print(reply[0].decode() +  ": File not found")
                        break
                    else:
                        if len(reply) != 2:
                            with open(command[1] + "_" + command[2], "wb") as f:
                                f.write(reply[2])

                        else:
                            open(command[1] + "_" + command[2], "a").close()
                        print(f"File {command[1]} downloaded")
                
                if failedFlag == len(all_replies):
                    print("File not found in all servers")
                print("")        
            else:
                for server in client.server_list:
                    server_reply = client.send_request(server, bytes_command)
                    all_replies.append(server_reply)

        except Exception as e:
            print(f"E: {e}")
            sys.exit(1)
