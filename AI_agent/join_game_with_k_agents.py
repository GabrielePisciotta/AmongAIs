import datetime as dt
import multiprocessing
from components.chat_analyzer import ChatAnalyzer
from components.algorithms.fuzzy.fuzzy_action_manager import FuzzyActionManager
from components.algorithms.fuzzy.fuzzy_impostor_analyzer import FuzzyImpostorAnalyzer
from components.algorithms.reinforcement.rl_motion_analyzer import QLearnerMotionAnalyzer
from components.algorithms.graphs.graph_motion_analyzer import GraphMotionAnalyzer
from components.algorithms.simple.simple_shoot_analyzer import SimpleShootAnalyzer
from components.algorithms.simple.simple_action_manager import SimpleActionManager
from components.algorithms.simple.map_tiled import MapPrinter
from components.network_manager import NetworkManager
from components.chat_handler import ChatHandler
from components.components import MapAnalyzer
from ai_agent import AI_Agent
from pygame.locals import *
from config import *
import pygame
import time
import uuid
import os
import sys
from datetime import datetime
import traceback
traceback.print_exc()
sys.path.append('..')

class Logger(object):
    def __init__(self, agent_name):
        self.log_file_name = f"logs/{agent_name}_game_{datetime.timestamp(datetime.now())}.log"
        self.terminal = sys.stdout
        if LOGGING_ON:
            if os.path.exists(self.log_file_name):
                os.remove(self.log_file_name)
            if not os.path.exists("logs"):
                os.makedirs("logs/")
            self.log = open(self.log_file_name, "a")

    def write(self, message):
        # self.terminal.write(message)
        if LOGGING_ON:
            self.log.write(message)

    def flush(self):
        pass




def create_agent(name, radius=0):
    action_manager = None
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


def action(name, type, q):
    a = create_agent(name, type)
    a.join_game()
    a.join_channel(SERVER_GAME_NAME)

    # compute flag danger radius
    radius = a.get_flag_radius()
    a.set_flag_radius(radius)
    print(f"Flag danger radius={radius}")

    sys.stdout = Logger(name)

    a.post_to_channel(SERVER_GAME_NAME, "Good game to everybody!")
    a.action_manager.network_manager.update_delay(SERVER_DELAY_SEC_AFTER_JOIN)

    while not a.is_game_active():
        continue
    a.action_manager.start_match_time = datetime.now()
    while a.is_game_active():
        a.action()

    q.put("end")


def main():

    try:

        mgr = multiprocessing.Manager()
        q = mgr.Queue()

        processes = []
        for a in AGENTS:
            name, type = a
            processes.append(multiprocessing.Process(
                target=action, args=(name, type, q)))
            processes[-1].start()
            time.sleep(0.6)

        while(q.empty()):
            continue

    except Exception as e:
        print(f"Exception {e}, die")
        exit()


if __name__ == "__main__":
    main()
