import sys
import telnetlib
import datetime
import queue
import socket
import multiprocessing
from selectors import select

sys.path.append('..')
from config import *
import errno


class ChatHandler(object):
    """Manage the interaction with the Chat Server.
    """

    def __init__(self, public_name):
        mgr = multiprocessing.Manager()
        self.queue = mgr.Queue()

        self.public_name = public_name
        self.messages = mgr.list()

        if DEBUG:
            print(f"{self.public_name} connected to Chat Server.")

        # Once we've put the name in the queue, we can send other commands
        # to the server, including JOIN and LEAVE channel or POST messages to.
        name = {
            "command": f"NAME {public_name}"
        }
        self.queue.put(name)

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((SERVER_HOST, CHAT_SERVER_PORT))
        self.s.setblocking(1)

        self.write_process = multiprocessing.Process(target=write_chat, args=(self.s, self.queue,))
        self.write_process.daemon = True
        self.write_process.start()

        self.read_process = multiprocessing.Process(target=read_chat, args=(self.s, self.messages,))
        self.read_process.daemon = True
        self.read_process.start()

    def get_messages(self):
        return list(self.messages)

    def send_command(self, cmd: str):
        """Send command to the Chat Server.

        Parameters
        ----------
        cmd : str
            the command to be sent.
        """

        # This is the request object that will be stored in the queue
        request = {
            "command": cmd
        }

        # Add it to the queue
        self.queue.put(request)

    def stop_queue(self):
        request = {
            "command": "STOP QUEUE"
        }

        if self.queue is not None:
            try:
                self.queue.put(request)
                self.read_process.kill()
            except:
                pass

    def __del__(self):
        self.stop_queue()


def write_chat(s, queue) -> None:
    """This method consume concurrently the queue while reading the messages written in chat.
    """
    last_time_message_sent = datetime.datetime.now()

    # We exploit `CHAT_SERVER_NOP_SEC` in the config file to send a NOP
    # to #NOP channel for not being disconnected from the Server after
    # 5 mins of inactivity.

    while True:

        _, writable, _ = select.select([], [s], [])
        for sock in writable:

            now = datetime.datetime.now()
            delta = now - last_time_message_sent
            seconds_passed = int(delta.total_seconds())

            if queue.empty():
                if seconds_passed > CHAT_SERVER_NOP_SEC:
                    cmd = f"{NOP_CH} NOP"
                else:
                    continue
            else:
                try:
                    request = queue.get()
                    cmd = request["command"]

                    if cmd == "STOP QUEUE":
                        return
                except:
                    None
            print(f"Sending {cmd}")
            sock.sendall(cmd.encode('utf-8') + b'\n')
            last_time_message_sent = datetime.datetime.now()


def read_chat(s, messages) -> None:
    while True:
        readable, _, _ = select.select([s], [], [])
        for sock in readable:
            read_until = True
            buffer = ''
            while read_until:
                # Try to receive some data
                buffer += sock.recv(2048).decode('utf-8')

                if "\n" in buffer:
                    messages.append(buffer)
                    read_until = False
