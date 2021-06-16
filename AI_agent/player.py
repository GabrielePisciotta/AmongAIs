import abc
import numpy as np
from config import *
from components import *
from components.entity import *


class PlayerInterface(abc.ABC):
    """Base components of a Player.
    """

    def __init__(self, name, action_manager):
        self.name = name
        self.action_manager = action_manager
        self.game_started = False
        self.game_finished = False
    
    def join_game(self):
        try:
            res = self.action_manager.network_manager.send_command(
                f"{SERVER_GAME_NAME} JOIN {self.name} AI - {USER_INFO}")
            return ("OK" in res)

        except Exception:
            return False

    def is_game_active(self):
        msgs = self.action_manager.chat_handler.get_messages()
        for m in msgs:
            if not self.game_started and m == f'{SERVER_GAME_NAME} @GameServer Now starting!\n':
                self.game_started = True
            if not self.game_finished and m.startswith(f'{SERVER_GAME_NAME} @GameServer Game finished!'):
                self.game_finished = True

        if self.game_started and not self.game_finished:
            return True
        else:
            return False


    def start_game(self):
        try:
            res = self.action_manager.network_manager.send_command(
                f"{SERVER_GAME_NAME} START")
            return ("OK" in res)
        except Exception:
            return False

    def join_channel(self, channel):
        """This method allows a user to join an existing channel on the Chat Server
        or to create a new one if it doesn't exist.
        No response is expected from the Chat Server.

        Parameters
        ----------
        channel : str
            the channel to be joined.
        """
        self.action_manager.chat_handler.send_command(f"JOIN {channel}")
        if DEBUG:
            print(f"{self.name} connected to channel {channel}")

    def leave_channel(self, channel):
        """This method allows a user to leave an existing channel on the Chat Server.

        Parameters
        ----------
        channel : str
            the channel to be left.
        """
        self.action_manager.chat_handler.send_command(f"LEAVE {channel}")
        if DEBUG:
            print("Disconnected from: " + channel)

    def post_to_channel(self, channel, text):
        """This method allows a user to post a message to a channel on the Chat Server.

        Parameters
        ----------
        channel : str
            the channel to be left.

        text: str
            the text of the message to be posted.
        """
        self.action_manager.chat_handler.send_command(f"POST {channel} {text}")
        if DEBUG:
            print(f"{self.name} write '{text}' to channel '{channel}'")
    
    def send_command(self, cmd):
        return self.action_manager.network_manager.send_command(cmd)
    
    def stop_play(self):
        self.action_manager.network_manager.stop_queue()
        self.action_manager.chat_handler.stop_queue()
    
    def get_flag_radius(self):
        status = self.action_manager.retrieve_game_status()
        size = int(status.size)
        ratio = status.ratio  # Q or W

        if size == 32:
            if ratio == 'Q':
                return SMALL_FLAG_RADIUS_Q
            else:
                return SMALL_FLAG_RADIUS_W
        elif size == 64:
            if ratio == 'Q':
                return MEDIUM_FLAG_RADIUS_Q
            else:
                return MEDIUM_FLAG_RADIUS_W
        else:
            if ratio == 'Q':
                return BIG_FLAG_RADIUS_Q
            else:
                return BIG_FLAG_RADIUS_W

    def set_flag_radius(self, radius):
        self.action_manager.FLAG_DANGER_RADIUS = radius

    @abc.abstractmethod
    def action(self, status):
        """Gives the action to do.

        Returns
        -------
        str
            the next action
        """
        pass
