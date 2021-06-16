from pygame.constants import K_CLEAR
from components.algorithms.fuzzy.fuzzy_action_manager import FuzzyActionManager
from components.algorithms.fuzzy.fuzzy_impostor_analyzer import FuzzyImpostorAnalyzer
from components.algorithms.reinforcement.rl_motion_analyzer import QLearnerMotionAnalyzer
from components.algorithms.graphs.graph_motion_analyzer import GraphMotionAnalyzer
from components.algorithms.simple.simple_shoot_analyzer import SimpleShootAnalyzer
from components.algorithms.simple.simple_action_manager import SimpleActionManager
from components.algorithms.simple.map_tiled import MapPrinter
from components.network_manager import NetworkManager
from components.chat_handler import ChatHandler
from components.chat_analyzer import ChatAnalyzer
from components.components import MapAnalyzer
from ai_agent import AI_Agent
# from pygame.locals import *
from config import *
# import pygame
import time
import uuid
import os
import sys
import traceback
from datetime import datetime
traceback.print_exc()
sys.path.append('..')


base_string = "AI7-Player-"


class Logger(object):
    def __init__(self):
        self.log_file_name = f"logs/game_{datetime.timestamp(datetime.now())}.log"
        self.terminal = sys.stdout
        if LOGGING_ON:
            if os.path.exists(self.log_file_name):
                os.remove(self.log_file_name)
            if not os.path.exists("logs"):
                os.makedirs("logs/")
            self.log = open(self.log_file_name, "a")

    def write(self, message):
        self.terminal.write(message)
        if LOGGING_ON:
            self.log.write(message)  

    def flush(self):
        pass


def create_agent(name, radius=0):
    motion_analyzer = None
    if DEFAULT_AGENT == "graph":
        motion_analyzer = GraphMotionAnalyzer(name)
    elif DEFAULT_AGENT == "rl":
        motion_analyzer = QLearnerMotionAnalyzer(
            lr=0.99,
            num_episodes=1000,
            epsilon=0.35,
            epsilon_decay=0.00001,
            gamma=0.99,
            max_iters=1000
        )

    action_manager = FuzzyActionManager(
        network_manager=NetworkManager(),
        chat_handler=ChatHandler(name),
        motion_analyzer=motion_analyzer,
        map_analyzer=MapAnalyzer(),
        shoot_analyzer=SimpleShootAnalyzer(),
        chat_analyzer=ChatAnalyzer(),
        impostor_analyzer=FuzzyImpostorAnalyzer(),
        flag_danger_radius=radius
    )
    
    return AI_Agent(name=name, action_manager=action_manager)


def main():
    sys.stdout = Logger()

    idx = 0
    agents = []
    creator = create_agent(base_string+str(idx))
    idx += 1
    agents.append(creator)
    try:
        print(f"Game name: {SERVER_GAME_NAME}")

        # Create the game
        if not creator.join_game():
            print(
                "Cannot join, maybe the game must be created. Creating game... ", end="")
            if TRAINING:
                creator.send_command(f"NEW {SERVER_GAME_NAME} T")
            else:
                creator.send_command(f"NEW {SERVER_GAME_NAME}")
            done = creator.join_game()
            creator.join_channel(SERVER_GAME_NAME)

            if done:
                print("Done")
            else:
                creator.stop_play()
                exit()
        
        # compute flag danger radius
        radius = creator.get_flag_radius()
        creator.set_flag_radius(radius)

        # Manage the lobby state (wait 'til agents in the game)
        # --> Basically we add agents iteratively
        input("\n>> Press ENTER to start the game . . . ")
        started = False
        while not started:
            #creator.post_to_channel(NOP_CH, "ping")
            # Create random agent name
            agent_name = base_string+str(idx)
            idx += 1
            # Add it to a list
            agents.append(create_agent(agent_name, radius))
            # Let the last added join the game
            join = agents[-1].join_game()
            agents[-1].join_channel(SERVER_GAME_NAME)
            print(f"{agent_name} added in the lobby: {join}")

            time.sleep(1)

            # Start the game
            print("Trying to start: ", end="")
            result = creator.send_command(f"{SERVER_GAME_NAME} START")
            if "OK" in result:
                print("OK")
                started = True
            else:
                print("Need another agent in the game")

        creator.post_to_channel(SERVER_GAME_NAME, "Good game to everybody!")
        time.sleep(2)
        for agent in agents:
            agent.action_manager.network_manager.update_delay(SERVER_DELAY_SEC_AFTER_JOIN)

        while creator.is_game_active():
            if SINGLE_AGENT_MODE:
                agent = agents[0]
                print(f"\n----| {agent.name} |----")
                agent.action()
                # if DEBUG:
                #     agent.post_to_channel(
                #         SERVER_GAME_NAME, "Made a move, be careful ya!")
                agent.post_to_channel(NOP_CH, "")
            else:
                for i, agent in enumerate(agents):
                    print(f"\n----| {agent.name} |----")
                    agent.action()
                    # if DEBUG:
                    #     agent.post_to_channel(
                    #         SERVER_GAME_NAME, "Made a move, be careful ya!")
                    agent.post_to_channel(NOP_CH, "")
    except Exception as e:
        e.with_traceback()
        exit()


if __name__ == "__main__":
    main()
