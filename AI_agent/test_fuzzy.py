import matplotlib.pyplot as plt
import skfuzzy
from skfuzzy import control as ctrl
from config import *
import numpy as np
import os
import sys
from tqdm import tqdm


def test_action_mgr():
    ###############
    # ANTECEDENTS #
    ###############
    aggressive = ctrl.Antecedent(np.arange(0, 5, .1), 'aggressive')
    aggressive['no'] = skfuzzy.trimf(aggressive.universe, [0, 0, 1])
    aggressive['yes'] = skfuzzy.sigmf(aggressive.universe, 1, 4)
    # percentage of enemies nearby the flag
    myflag_danger = ctrl.Antecedent(np.arange(0, 101, 10), 'myflag_danger')
    myflag_danger['low'] = skfuzzy.trimf(
        myflag_danger.universe, [0, 0, 50])
    myflag_danger['medium'] = skfuzzy.trimf(
        myflag_danger.universe, [0, 50, 100])
    myflag_danger['high'] = skfuzzy.trimf(
        myflag_danger.universe, [50, 100, 100])

    max_energy = 256
    mid_energy = int(max_energy / 2)
    energy = ctrl.Antecedent(
        np.arange(0, max_energy + 1, 1), 'energy')
    energy['low'] = skfuzzy.trimf(energy.universe, [0, 0, mid_energy])
    energy['medium'] = skfuzzy.trimf(
        energy.universe, [0, mid_energy, max_energy])
    energy['high'] = skfuzzy.trimf(
        energy.universe, [mid_energy, max_energy, max_energy])

    ###############
    # CONSEQUENTS #
    ###############
    move = ctrl.Consequent(np.arange(0, 101, 10), 'move')
    move['low'] = skfuzzy.trimf(move.universe, [0, 0, 50])
    move['medium'] = skfuzzy.trimf(move.universe, [0, 50, 100])
    move['high'] = skfuzzy.trimf(move.universe, [50, 100, 100])

    shoot = ctrl.Consequent(np.arange(0, 101, 10), 'shoot')
    shoot['low'] = skfuzzy.trimf(shoot.universe, [0, 0, 50])
    shoot['medium'] = skfuzzy.trimf(shoot.universe, [0, 50, 100])
    shoot['high'] = skfuzzy.trimf(shoot.universe, [50, 100, 100])

    accuse = ctrl.Consequent(np.arange(0, 101, 10), 'accuse')
    accuse['no'] = skfuzzy.trimf(accuse.universe, [0, 0, 70])
    accuse['yes'] = skfuzzy.trimf(accuse.universe, [60, 100, 100])

    mode = ctrl.Consequent(np.arange(0, 101, 10), 'mode')
    mode['defense'] = skfuzzy.trimf(mode.universe, [0, 0, 60])
    mode['attack'] = skfuzzy.trimf(mode.universe, [40, 100, 100])

    aggressive.view()
    myflag_danger.view()
    energy.view()
    move.view()
    shoot.view()
    accuse.view()
    mode.view()

    # rules_set = [
    #     # move rules
    #     ctrl.Rule(aggressive['yes'] | myflag_danger['low']
    #                 | energy['low'], move['high']),
    #     ctrl.Rule(aggressive['yes'] | myflag_danger['medium']
    #                 | energy['medium'], move['medium']),
    #     ctrl.Rule(aggressive['no'] | myflag_danger['high']
    #                 | energy['high'], move['low']),
    #     # shoot rules
    #     ctrl.Rule(aggressive['yes'] & energy['high'], shoot['high']),
    #     ctrl.Rule(aggressive['yes'] & energy['medium'], shoot['high']),
    #     ctrl.Rule(aggressive['yes'] & energy['low'], shoot['low']),
    #     ctrl.Rule(aggressive['no'] | myflag_danger['high']
    #                 | energy['low'], shoot['low']),
    #     # accuse rules
    #     ctrl.Rule(aggressive['no'] & myflag_danger['low']
    #                 & energy['low'], accuse['yes']),
    #     ctrl.Rule(aggressive['no'] | myflag_danger['low']
    #                 | energy['low'], accuse['no']),
    #     ctrl.Rule(aggressive['yes'] | myflag_danger['medium']
    #                 | energy['low'], accuse['no']),
    #     ctrl.Rule(aggressive['yes'] | myflag_danger['high']
    #                 | energy['low'], accuse['no']),
    #     # attack rules
    #     ctrl.Rule(aggressive['yes'] |
    #                 myflag_danger['low'], mode['attack']),
    #     ctrl.Rule(aggressive['no'] & (
    #         myflag_danger['medium'] | myflag_danger['high']), mode['defense'])
    # ]

    # system_ctrl = ctrl.ControlSystem(rules=rules_set)
    # system = ctrl.ControlSystemSimulation(system_ctrl)

    # if os.path.exists("fuzzy_action_mgr_rules.txt"):
    #     os.remove("fuzzy_action_mgr_rules.txt")
    # file = open("fuzzy_action_mgr_rules.txt", "a")

    # with tqdm(total=(4*100*max_energy)) as pbar:
    #     for a in range(0, 4):
    #         for d in range(0, 101):
    #             for e in range(0, max_energy+1):
    #                 system.input['aggressive'] = a
    #                 system.input['myflag_danger'] = d
    #                 system.input['energy'] = e

    #                 print(f"Aggressive = {a}", file=file)
    #                 print(f"My Flag Danger = {d}", file=file)
    #                 print(f"Energy = {e}", file=file)

    #                 system.compute()

    #                 print(f"Moving = {system.output['move']}%", file=file)
    #                 print(f"Shooting = {system.output['shoot']}%", file=file)
    #                 print(f"Accuse = {system.output['accuse']}%", file=file)
    #                 print(f"Attack = {system.output['attack']}%\n", file=file)
    #                 pbar.update(1)


def test_impostor():
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
    system = ctrl.ControlSystemSimulation(system_ctrl)

    if os.path.exists("fuzzy_impostor_rules.txt"):
        os.remove("fuzzy_impostor_rules.txt")
    file = open("fuzzy_impostor_rules.txt", "a")

    with tqdm(total=(10*10*100*10)) as pbar:
        for a_dist in range(0, 101, 10):
            for e_dist in range(0, 101, 10):
                for a_kill in range(0, 101, 1):
                    for e_kill in range(0, 101, 10):
                        system.input['ally_flag_distance'] = a_dist
                        system.input['enemy_flag_distance'] = e_dist
                        system.input['ally_killed'] = a_kill
                        system.input['enemy_killed'] = e_kill

                        print(f"Ally Flag Distanse = {a_dist}", file=file)
                        print(f"Enemy Flag Distanse = {e_dist}", file=file)
                        print(f"Allies Killed = {a_kill}", file=file)
                        print(f"Enemies Killed = {e_kill}\n", file=file)

                        system.compute()

                        print(
                            f"Impostor = {system.output['impostor']}%", file=file)
                        pbar.update(1)


if __name__ == "__main__":
    test_action_mgr()
    # test_impostor()
