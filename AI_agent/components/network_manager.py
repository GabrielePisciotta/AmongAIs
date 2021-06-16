import multiprocessing
from utils import run_in_thread
from config import *
import datetime
import queue
import sys
import time
import uuid
from copy import deepcopy
from requests import Timeout
import socket
import select  # pip install selectors
import errno

sys.path.append('..')


class NetworkManager(object):
    """Manage the interaction with the Game Server.
    """

    def __init__(self):
        self.m = multiprocessing.Manager()
        self.queue = self.m.Queue()
        self.results = self.m.dict()
        self.p = multiprocessing.Process(target=consume_queue, args=(
            self.queue, self.results, SERVER_DELAY_SEC))
        self.p.daemon = True
        self.p.start()

    def update_delay(self, delay):

        request = {
            "request_id": None,
            "command": f"DELAY {delay}"
        }
        self.queue.put(request)


    def send_command(self, cmd: str) -> str:
        """Send command to the Game Server.
        We encapsulate the command in a request object that will be stored in a queue. 
        We manage both the possibility that the computation of the request exceed 
        our max awaitable time and the possibility that the server gives us a connection error. 
        To do that, we refers to CMD_REQUEST_TIMEOUT and MAX_RESEND in the config file.

        Parameters
        ----------
        cmd : str
            the command to be sent.

        Returns
        -------
        str
            the response body.

        Raises
        ------
        Timeout : if no results obtained.
        """

        resended = 0
        while resended < MAX_RESEND:
            # In order to assign a random unique ID to the request we exploit a UUID string
            request_id = str(uuid.uuid4())

            # This is the request object that will be stored in the queue
            request = {
                "request_id": request_id,
                "command": cmd
            }

            # Add it to the queue
            self.queue.put(request)

            # Once we've put the request in the queue, we have to wait a certain
            # amount of time until it became processed.
            # We exploit `CMD_REQUEST_TIMEOUT` in the config file to set this time.
            # If we get no results when the time expires,
            # it will be re-sent until `MAX_RESEND`.
            start = datetime.datetime.now()
            now = datetime.datetime.now()

            while (now - start).total_seconds() < CMD_REQUEST_TIMEOUT_SEC:

                # Return the results if it's been computed and it's different
                # from a connection closed response from the server
                if self.results.__contains__(request_id):
                    if self.results[request_id] == CONNECTION_CLOSED:
                        print(CONNECTION_CLOSED)
                        break
                    else:
                        result = deepcopy(self.results[request_id])
                        # del self.results[request_id]  # remove the result from the dict
                        return result
                now = datetime.datetime.now()

            # If we're here, it's because the command hasn't been computed and
            # we received a Timeout error from the server or we've found that
            # the request time exceded max awaitable time, so we'll resend
            resended += 1

        # if get here without any results and having resent the message many times,
        # just raise a timeout exception
        raise Timeout()

    def stop_queue(self):

        request = {
            "request_id": None,
            "command": "STOP QUEUE"
        }

        self.p.terminate()

    def __del__(self):
        self.stop_queue()


def consume_queue(queue, results, delay) -> None:
    """This method consume concurrently the queue, storing the result of
    the request in the results' dict.
    """
    last_time_message_sent = datetime.datetime.now()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_HOST, SERVER_PORT))
        s.setblocking(0)
        while True:

            # We can send a request each delay time specified by the server (e.g.: 500ms).
            # We store this value in the variable SERVER_DELAY_MILLISEC in the config file.
            # So we compute the difference between the time when the last command
            # has been sent and 'now', and verify that the difference exceeds
            # 500ms in order to avoid to have our command rejected by the server.
            now = datetime.datetime.now()
            delta = now - last_time_message_sent
            seconds_passed = delta.total_seconds()

            if seconds_passed > delay:

                if queue.empty() and seconds_passed >= SERVER_NOP_SEC:
                    cmd = f"{SERVER_GAME_NAME} NOP"
                    request_id = str(uuid.uuid4())
                    s.sendall(cmd.encode('ascii') + b'\n')
                    last_time_message_sent = datetime.datetime.now()

                elif not queue.empty():
                    request = queue.get()
                    cmd = request["command"]
                    request_id = request["request_id"]

                    if cmd == "STOP QUEUE":
                        return
                    elif "DELAY" in cmd:
                        delay_msg_chunks = cmd.split(" ")
                        delay = float(delay_msg_chunks[1])
                        results[request_id] = "Changed delay"
                        continue

                    s.sendall(cmd.encode('ascii')+b'\n')
                    for_the_error_if_happens = last_time_message_sent

                    # The socket have data ready to be received
                    buffer = ''
                    while True:
                        try:
                            # Try to receive som data
                            buffer += s.recv(2048).decode('utf-8')
                            last_time_message_sent = datetime.datetime.now()

                            if "ENDOFMAP" in buffer:
                                results[request_id] = buffer.replace(
                                    "\n«ENDOFMAP»", "")
                                break
                            elif "ENDOFSTATUS" in buffer:
                                results[request_id] = buffer.replace(
                                    "\n«ENDOFSTATUS»", "")
                                break

                            elif "JOIN" in cmd or "NEW" in cmd or "START" in cmd or "SHOOT" in cmd or "MOVE" in cmd or "ACCUSE" in cmd or "JUDGE" in cmd:
                                if "OK" in buffer or "ERROR" in buffer:
                                    results[request_id] = buffer
                                    break
                            elif "NOP" in cmd and "\n" in buffer:
                                results[request_id] = buffer
                                break

                            elif CONNECTION_CLOSED in buffer:
                                print(CONNECTION_CLOSED)
                                results[request_id] = CONNECTION_CLOSED
                                break

                            elif "Too fast" in buffer:
                                print(
                                    f"Too fast!!! {(last_time_message_sent-for_the_error_if_happens).total_seconds()}")
                                results[request_id] = CONNECTION_CLOSED
                                time.sleep(1)
                                break

                        except socket.error as e:
                            if e.errno != errno.EWOULDBLOCK:
                                print(f"Error: {e}")
                                raise Exception("Errore nella socket!")
