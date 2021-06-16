import sys
sys.path.append('..')
from config import *
import random
from components.entity import *
from components.components import ActionManagerInterface
from components.components import ChatAnalyzerInterface


class SimpleActionManager(ActionManagerInterface):
    """Action Manager based on random choice"""

    def __init__(self,
                 shoot_analyzer=None,
                 motion_analyzer=None,
                 map_analyzer=None,
                 objects_analyzer=None,
                 impostor_analyzer=None,
                 network_manager=None,
                 scoring_system=None,
                 chat_handler=None,
                 chat_analyzer=None):
        self.first_time = True
        self.possible_actions = []
        super(SimpleActionManager, self).__init__(
            shoot_analyzer,
            motion_analyzer,
            map_analyzer,
            objects_analyzer,
            impostor_analyzer,
            network_manager,
            scoring_system,
            chat_handler,
            chat_analyzer
        )

    def _check_can_shoot(self):
        direction_can_shot = self.shoot_analyzer.analyze(self.map_snapshot) #<-- qui dovremmo passare lo snapshot o una sua predizione
        if direction_can_shot:
            self.possible_actions.append([self.shoot, direction_can_shot])
            return True

    def _check_can_move(self):
        direction_can_move = self.motion_analyzer.analyze(snapshot=None)
        if direction_can_move:
            self.possible_actions.append([self.move, direction_can_move])
            return True
    
    def must_refresh_status(self):
        if self.first_time:
            self.first_time = False
            return True
        return True if random.random() < 0.1 else False

    def set_status(self):
        """ Retrieve the status from the game
        """

        self.map_snapshot = self.map_analyzer.analyze(self.retrieve_game_status())
        self.game_chat = self.chat_analyzer.analyze(self.retrieve_chat_status())

        self.possible_actions = []

        # Check if we can shot right now
        direction_can_shot = self._check_can_shoot()
        if direction_can_shot:
            self.possible_actions.append([self.shoot, direction_can_shot])

        # Otherwise compute the next moves
        else:
            direction_can_move = self.motion_analyzer.analyze(snapshot=self.map_snapshot)
            self.possible_actions.append([self.move, direction_can_move])

    def move(self, direction):
        move = self.network_manager.send_command(f"{SERVER_GAME_NAME} MOVE {direction}")
        if DEBUG and "OK" in move:
            print(f"\tGo to {direction}, from {self.map_snapshot.xy_me}: {move}")
        else:
            print("\tNot moving")

    def shoot(self, direction):
        if direction:
            shot = self.network_manager.send_command(f"{SERVER_GAME_NAME} SHOOT {direction}")
            if DEBUG:
                print(f"\tSHOOT RESULT: {shot}")
        else:
            print("\tCan't shoot")

    def next_action(self):

        if len(self.possible_actions) == 0:
            self._check_can_move()

        # Get the action and its argument (e.g.: move(), 'E')
        if len(self.possible_actions):
            action, argument = self.possible_actions.pop(0)

            # Execute it
            action(argument)
