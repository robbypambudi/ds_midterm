import os

HIDDEN_FILES_REGEX = r"^\..*"
SHARED_DIR = "shared"

# if len(sys.argv) < 2:
#     print(f"I: Syntax: {sys.argv[0]} <endpoint>")
#     sys.exit(0)


def list_all_files(include_hidden=False):
    current_dir = os.curdir

    for path, subdirs, files in os.walk(current_dir):
        print(path, subdirs, files)

    return


list_all_files()


# endpoint = sys.argv[1]
# context = zmq.Context()
# server = context.socket(zmq.REP)
# server.bind(endpoint)
#
# print(f"I: Echo service is ready at {endpoint}")
# while True:
#     msg = server.recv_multipart()
#     if not msg:
#         break
#     server.send_multipart(msg)
#
# server.setsockopt(zmq.LINGER, 0)
