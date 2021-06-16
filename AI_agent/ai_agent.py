from player import PlayerInterface
from config import *
import random
import uuid


class AI_Agent(PlayerInterface):
    """Player using AI algorithm to move in a grid-world.
    """

    def __init__(self,
                 name=f"ai_agent_{str(uuid.uuid4())}",
                 action_manager=None):
        super(AI_Agent, self).__init__(
            name=name,
            action_manager=action_manager
        )

    def action(self):
        if self.action_manager.must_refresh_status():
            self.action_manager.set_status()  # pass the status to the action manager
        self.action_manager.next_action()  # do the next action

    def __del__(self):
        self.action_manager.network_manager.stop_queue()
        self.action_manager.chat_handler.stop_queue()
