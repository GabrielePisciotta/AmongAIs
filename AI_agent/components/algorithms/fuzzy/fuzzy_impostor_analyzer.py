from components.components import ImpostorAnalyzerInterface
from components.entity import *
from config import *
import sys
import time
import skfuzzy
import numpy as np
from skfuzzy import control as ctrl
import operator
import random

sys.path.append('..')


class FuzzyImpostorAnalyzer(ImpostorAnalyzerInterface):

    def __init__(self):
        self.THRESHOLD_IMPOSTOR = 0.8
        ###############
        # ANTECEDENTS #
        ###############
        ally_flag_distance = ctrl.Antecedent(
            np.arange(0, 101, 1), 'ally_flag_distance')
        ally_flag_distance['high'] = skfuzzy.trimf(
            ally_flag_distance.universe, [0, 0, 50])
        ally_flag_distance['medium'] = skfuzzy.trimf(
            ally_flag_distance.universe, [0, 50, 100])
        ally_flag_distance['low'] = skfuzzy.trimf(
            ally_flag_distance.universe, [50, 100, 100])

        enemy_flag_distance = ctrl.Antecedent(
            np.arange(0, 101, 1), 'enemy_flag_distance')
        enemy_flag_distance['high'] = skfuzzy.trimf(
            enemy_flag_distance.universe, [0, 0, 50])
        enemy_flag_distance['medium'] = skfuzzy.trimf(
            enemy_flag_distance.universe, [0, 50, 100])
        enemy_flag_distance['low'] = skfuzzy.trimf(
            enemy_flag_distance.universe, [50, 100, 100])

        ally_killed = ctrl.Antecedent(np.arange(0, 101, 1), 'ally_killed')
        ally_killed['no'] = skfuzzy.trimf(ally_killed.universe, [0, 0, 0.1])
        ally_killed['yes'] = skfuzzy.sigmf(ally_killed.universe, 0.1, 100)

        enemy_killed = ctrl.Antecedent(np.arange(0, 101, 1), 'enemy_killed')
        enemy_killed['high'] = skfuzzy.trimf(enemy_killed.universe, [0, 0, 50])
        enemy_killed['medium'] = skfuzzy.trimf(
            enemy_killed.universe, [0, 50, 100])
        enemy_killed['low'] = skfuzzy.trimf(
            enemy_killed.universe, [50, 100, 100])

        ##############
        # CONSEQUENT #
        ##############
        impostor = ctrl.Consequent(np.arange(0, 101, 10), 'impostor')
        impostor['low'] = skfuzzy.trimf(impostor.universe, [0, 0, 50])
        impostor['medium'] = skfuzzy.trimf(impostor.universe, [0, 50, 100])
        impostor['high'] = skfuzzy.trimf(impostor.universe, [50, 100, 100])

        ally_flag_distance.view()
        enemy_flag_distance.view()
        ally_killed.view()
        enemy_killed.view()

        rules_set = [
            ctrl.Rule(ally_killed['yes'], impostor['high']),
            ctrl.Rule(ally_flag_distance['high'] | enemy_flag_distance['low']
                    | enemy_killed['low'], impostor['high']),
            ctrl.Rule(ally_flag_distance['medium'] | enemy_flag_distance['medium']
                    | ally_killed['no'] | enemy_killed['medium'], impostor['medium']),
            ctrl.Rule(ally_flag_distance['low'] | enemy_flag_distance['high']
                    | ally_killed['no'] | enemy_killed['high'], impostor['low'])
        ]

        system_ctrl = ctrl.ControlSystem(rules=rules_set)
        self.system = ctrl.ControlSystemSimulation(system_ctrl)

    def __compute_ally_flag_distance(self, ally_flag, enemy_flag, player_coord):
        """Computes the distance ratio between player and ally flag.

        Parameters
        ----------
        ally_flag : (int,int)
            the coordinates of player flag.
        enemy_flag : (int,int)
            the coordinater of player enemy flag.
        player_coord : (int,int)
            the coordinates of the player.

        Returns
        -------
        float
            (dist(ally_flag) / [dist(ally_flag) + dist(enemy_flag)]) * 100
        """
        me_coord = np.array(list(player_coord))
        my_flag_coord = np.array(list(ally_flag))
        enemy_flag_coord = np.array(list(enemy_flag))

        dist_my_flag = np.linalg.norm(my_flag_coord - me_coord)
        dist_enemy_flag = np.linalg.norm(enemy_flag_coord - me_coord)
        return (dist_my_flag / (dist_my_flag + dist_enemy_flag)) * 100

    def __compute_enemy_flag_distance(self, ally_flag, enemy_flag, player_coord):
        """Computes the distance ratio between player and enemy flag.

        Parameters
        ----------
        ally_flag : (int,int)
            the coordinates of player flag.
        enemy_flag : (int,int)
            the coordinater of player enemy flag.
        player_coord : (int,int)
            the coordinates of the player.

        Returns
        -------
        float
            (dist(enemy_flag) / [dist(ally_flag) + dist(enemy_flag)]) * 100
        """
        me_coord = np.array(list(player_coord))
        my_flag_coord = np.array(list(ally_flag))
        enemy_flag_coord = np.array(list(enemy_flag))

        dist_my_flag = np.linalg.norm(my_flag_coord - me_coord)
        dist_enemy_flag = np.linalg.norm(enemy_flag_coord - me_coord)
        return (dist_enemy_flag / (dist_my_flag + dist_enemy_flag)) * 100

    def __compute_ally_killed(self, chat_analysis, player_name):
        """Computes the percentage of allies killed.

        Parameters
        ----------
        chat_analysis : entity.ChatAnalysis
            the chat analysis.
        player_name : str
            the player name.

        Returns
        -------
        int
            number of killed allies
        """
        if player_name in chat_analysis.ally_kills:
            return chat_analysis.ally_kills[player_name]
        else:
            return 0

    def __compute_enemy_killed(self, chat_analysis, player_name):
        """Computes the percentage of enemies killed.

        Parameters
        ----------
        chat_analysis : entity.ChatAnalysis
            the chat analysis.
        player_name : str
            the player name.

        Returns
        -------
        int
            number of killed enemies
        """
        if player_name in chat_analysis.enemy_kills:
            return chat_analysis.enemy_kills[player_name]
        else:
            return 0

    def analyze(self, snapshot, chat_analysis):
        impostors = []
        """
        # we can accuse only teammates
        for e in snapshot.enemies_with_status:
            self.system.input['ally_flag_distance'] = self.__compute_ally_flag_distance(
                snapshot.xy_flag, snapshot.xy_my_flag, e.coord)
            self.system.input['enemy_flag_distance'] = self.__compute_enemy_flag_distance(
                snapshot.xy_flag, snapshot.xy_my_flag, e.coord)
            self.system.input['ally_killed'] = self.__compute_ally_killed(
                chat_analysis, e.coord)
            self.system.input['enemy_killed'] = self.__compute_enemy_killed(
                chat_analysis, e.coord)
            self.system.compute()
            p_impostor = self.system.output['impostor']
            if p_impostor >= self.THRESHOLD_IMPOSTOR:
                impostors.append(e)
        """

        max_impostor = None
        max_p_impostor = 0

        for a in snapshot.allies_with_status:
            ally_dist = self.__compute_ally_flag_distance(snapshot.xy_my_flag, snapshot.xy_flag, a.coord)
            enemy_dist = self.__compute_enemy_flag_distance(snapshot.xy_my_flag, snapshot.xy_flag, a.coord)
            ally_killed = self.__compute_ally_killed(chat_analysis, a.name)
            n_allies = len(snapshot.allies_with_status)
            enemy_killed = self.__compute_enemy_killed(chat_analysis, a.name)
            n_enemies = len(snapshot.enemies_with_status)

            self.system.input['ally_flag_distance'] = ally_dist
            self.system.input['enemy_flag_distance'] = enemy_dist
            self.system.input['ally_killed'] = (ally_killed / n_allies) * 100
            self.system.input['enemy_killed'] = (enemy_killed / n_enemies) * 100
            self.system.compute()
            p_impostor = self.system.output['impostor']
            if DEBUG:
                print(f"Ally distance: {ally_dist} - enemy distance: {enemy_dist} - ally killed: {ally_killed} -"
                      f" enemy killed: {enemy_killed} - P(impostor) = {p_impostor}")
            if p_impostor >= self.THRESHOLD_IMPOSTOR and p_impostor > max_p_impostor:
                max_p_impostor = p_impostor
                max_impostor = a

        return max_impostor
