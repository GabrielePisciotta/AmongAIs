from components.components import ActionManagerInterface
from components.entity import *
from config import *
import sys
import time
import skfuzzy
import numpy as np
from skfuzzy import control as ctrl
import operator
import random
import datetime
sys.path.append('..')
from operator import add


class FuzzyActionManager(ActionManagerInterface):
    """Action Manager based on fuzzy logic.
    """

    def __init__(self,
                 shoot_analyzer=None,
                 motion_analyzer=None,
                 map_analyzer=None,
                 impostor_analyzer=None,
                 network_manager=None,
                 chat_handler=None,
                 chat_analyzer=None,
                 energy=256,
                 flag_danger_radius=5):
        self.CHECK_TIME_DELAY = 0.9  # check status every second
        self.FLAG_DANGER_RADIUS = flag_danger_radius
        self.judged = False
        self.snapshot = None
        self.game_chat = None
        self.max_energy = energy
        self.time_prev_refresh = None
        self.time_shoot_cooldown = None
        self.time_flag_cooldown = None
        self.force_check = True
        self.curr_target_cell = None
        self.mode = "attack"
        self.enemies = []
        self.last_time_moved = None
        self.start_match_time = None
        self.already_accused = False

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

        mid_energy = int(self.max_energy / 2)
        energy = ctrl.Antecedent(
            np.arange(0, self.max_energy + 1, 1), 'energy')
        energy['low'] = skfuzzy.trimf(energy.universe, [0, 0, mid_energy])
        energy['medium'] = skfuzzy.trimf(
            energy.universe, [0, mid_energy, self.max_energy])
        energy['high'] = skfuzzy.trimf(
            energy.universe, [mid_energy, self.max_energy, self.max_energy])

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

        rules_set = [
            # move rules
            ctrl.Rule(aggressive['yes'] | myflag_danger['low']
                      | energy['low'], move['high']),
            ctrl.Rule(aggressive['yes'] | myflag_danger['medium']
                      | energy['medium'], move['medium']),
            ctrl.Rule(aggressive['no'] | myflag_danger['high']
                      | energy['high'], move['low']),
            # shoot rules
            ctrl.Rule(aggressive['yes'] & energy['high'], shoot['high']),
            ctrl.Rule(aggressive['yes'] & energy['medium'], shoot['high']),
            ctrl.Rule(aggressive['yes'] & energy['low'], shoot['low']),
            ctrl.Rule(aggressive['no'] | myflag_danger['high']
                      | energy['low'], shoot['low']),
            # accuse rules
            ctrl.Rule(aggressive['no'] & myflag_danger['low']
                      & energy['low'], accuse['yes']),
            ctrl.Rule(aggressive['no'] | myflag_danger['low']
                      | energy['low'], accuse['no']),
            ctrl.Rule(aggressive['yes'] | myflag_danger['medium']
                      | energy['low'], accuse['no']),
            ctrl.Rule(aggressive['yes'] | myflag_danger['high']
                      | energy['low'], accuse['no']),
            # attack rules
            ctrl.Rule(aggressive['yes'] |
                      myflag_danger['low'], mode['attack']),
            ctrl.Rule(aggressive['no'] & (
                myflag_danger['medium'] | myflag_danger['high']), mode['defense'])
        ]

        system_ctrl = ctrl.ControlSystem(rules=rules_set)
        self.system = ctrl.ControlSystemSimulation(system_ctrl)

        super(FuzzyActionManager, self).__init__(
            shoot_analyzer,
            motion_analyzer,
            map_analyzer,
            impostor_analyzer,
            network_manager,
            chat_handler,
            chat_analyzer
        )

    def __compute_aggressive(self):
        """Compute the aggressivity based on the number of shootable enemies.

        Returns
        -------
        int
            shootable enemies (maximum 4)
        """
        if (self.time_shoot_cooldown is None) or ((datetime.datetime.now() - self.time_shoot_cooldown).total_seconds() <= SHOOT_COOLDOWN_SEC):
            return 0

        # if (self.time_flag_cooldown is None) or ((time.time() - self.time_flag_cooldown) <= FLAG_COOLDOWN_SEC):
        #     return 1

        cells = self.shoot_analyzer.get_shootable_cells(self.snapshot)
        n_shootable = 0

        for enemy in self.snapshot.enemies_with_status:

            if enemy.active == 'ACTIVE':
                if (enemy.coord in cells.keys()):
                    self.__perform_shoot()
                    n_shootable += 1

        return n_shootable if n_shootable <= 4 else 4

    def __compute_flag_danger(self):
        """Compute percentage of danger of flag based 
        on the percentage of enemies nearby my flag.

        Returns
        -------
        float
            percentage of enemies in my flag radius 
            if closer to my flag w.r.t. the enemy flag,
            otherwise lowest percentage of danger.
        """
        me_coord = np.array(list(self.snapshot.xy_me))
        my_flag_coord = np.array(list(self.snapshot.xy_my_flag))
        enemy_flag_coord = np.array(list(self.snapshot.xy_flag))

        dist_my_flag = np.linalg.norm(my_flag_coord - me_coord)
        dist_enemy_flag = np.linalg.norm(enemy_flag_coord - me_coord)
        if self.snapshot.loyalty and dist_enemy_flag <= dist_my_flag:
            if DEBUG:
                print("MY FLAG IS NOT IMPORTANT RIGHT NOW!")
            return .0
        else:
            n_enemies_in_radius = 0
            enemies = [x.coord for x in self.snapshot.enemies_with_status if x.active == 'ACTIVE']

            tot_enemies = len(enemies)

            for enemy in enemies:
                enemy_coord = np.array(enemy)
                dist = np.linalg.norm(my_flag_coord - enemy_coord)
                if dist <= self.FLAG_DANGER_RADIUS:
                    n_enemies_in_radius += 1
            if DEBUG:
                print(f"ENEMIES IN FLAG RADIUS: {n_enemies_in_radius}")
            return (n_enemies_in_radius / (tot_enemies + 1e-21)) * 100

    def __compute_energy(self):
        e = self.snapshot.my_energy
        return e if e <= self.max_energy else self.max_energy

    def __get_max_action(self):
        """Get the next action with the highest probability.

        Returns
        -------
        str
            next action with maximum probability.
        """
        p_move = self.system.output['move']
        p_shoot = self.system.output['shoot']
        p_accuse = self.system.output['accuse']
        p_attack = self.system.output['mode']
        self.mode = "attack" if (p_attack >= 50) else "defense"
        probs = {"move": p_move, "shoot": p_shoot, "accuse": p_accuse}
        if DEBUG:
            print(
                f"P(move)={p_move} - P(shoot)={p_shoot} - P(accuse)={p_accuse} - P(attack)={p_attack}")
        max_action = max(probs.items(), key=operator.itemgetter(1))[0]
        return max_action

    def __get_target_cell(self):
        """Get the first walkable cell nearby my flag.

        Returns
        -------
        (int,int)
            enemy's flag position if the agent is in `attack` mode, 
            my flag position modified if the agent is in `defense` mode.
        """
        target_cell = None
        if self.mode == "attack":
            target_cell = self.snapshot.xy_flag
        else:
            target_cell = self.snapshot.xy_my_flag

        if DEBUG:
            print(
                f"Enemy Flag={self.snapshot.xy_flag}, Ally Flag={self.snapshot.xy_my_flag}, Target Cell={target_cell}")
        return target_cell


    def __force_check(self):
        self.force_check = True

    def __new_defense_target(self, my_flag):
        n_rows = len(self.snapshot.map)
        n_cols = len(self.snapshot.map[0])
        neighbors = []
        if my_flag[0] > 1:
            neighbors.append((my_flag[0] - 1, my_flag[1]))  # N cell
        if my_flag[0] < n_rows - 2:
            neighbors.append((my_flag[0] + 1, my_flag[1]))  # S cell
        if my_flag[1] > 1:
            neighbors.append((my_flag[0], my_flag[1] - 1))  # W cell
        if my_flag[1] < n_cols - 2:
            neighbors.append((my_flag[0], my_flag[1] + 1))  # E cell

        for n in neighbors:
            row, col = n[0], n[1]
            if self.snapshot.map[row][col] not in ["#"]:
                print(f"NEW DEFENSE TARGET: {n}")
                return n
        return random.choice(neighbors)

    def __perform_move(self):

        direction = self.motion_analyzer.analyze(self.snapshot)
        if direction is not None:
            move = self.network_manager.send_command(
                f"{SERVER_GAME_NAME} MOVE {direction}")

            print(f"Move: {move}")
            print(f"Direction: {direction}")
            if DEBUG and "OK" in move and not "blocked" in move:
                print(f"--MOVE {direction}")
                if direction == 'S':
                    self.snapshot.xy_me = tuple(list(map(add, self.snapshot.xy_me, (1,0))))
                elif direction == 'N':
                    self.snapshot.xy_me = tuple(list(map(add, self.snapshot.xy_me, (-1,0))))
                elif direction == 'W':
                    self.snapshot.xy_me = tuple(list(map(add, self.snapshot.xy_me, (0,-1))))
                elif direction == 'E':
                    self.snapshot.xy_me = tuple(list(map(add, self.snapshot.xy_me, (0,1))))

                if self.last_time_moved is None:
                    self.last_time_moved = datetime.datetime.now()
                else:
                    now = datetime.datetime.now()
                    print("-- 1 cell each {}".format((now - self.last_time_moved).total_seconds()))
                    self.last_time_moved = now
        else:
            if DEBUG:
                print("--NO MOVE")

    def __perform_shoot(self):
        direction = self.shoot_analyzer.analyze(self.snapshot)
        if direction:
            shot = self.network_manager.send_command(
                f"{SERVER_GAME_NAME} SHOOT {direction}")
            if DEBUG:
                print(f"--SHOOT {direction} {shot}")
        else:
            if DEBUG:
                print("--NO SHOOT")

    def __perform_accuse(self):

        pl = self.impostor_analyzer.analyze(self.snapshot, self.game_chat)
        if DEBUG:
            print(f"ACCUSE: {pl.name}")

        if pl:
            accuse = self.network_manager.send_command(
                f"{SERVER_GAME_NAME} ACCUSE {pl.name}")
            if DEBUG and "OK" in accuse:
                print(f"--ACCUSE {accuse}")
        else:
            if DEBUG:
                print("--NO ACCUSE")

    def __perform_judge(self):
        players = self.snapshot.allies_with_status + self.snapshot.enemies_with_status
        mean_speeds = {}
        start = datetime.datetime.now()
        speeds = []

        for pl in players:
            mean_speeds[pl.name] = np.mean(pl.speed)
            speeds.append(mean_speeds[pl.name])

        threshold = np.percentile(speeds, 25) # filter on the first quartile

        for pl in players:
            nature = 'H' if mean_speeds[pl.name] <= threshold else 'AI'
            judge = self.network_manager.send_command(
                f"{SERVER_GAME_NAME} JUDGE {pl.name} {nature}")
            if DEBUG and "OK" in judge:
                print(f"--JUDGE {pl.name} {nature} {judge} | speed: {mean_speeds[pl.name]} threshold {threshold}")
            else:
                if DEBUG:
                    print("--NO JUDGE")
        end = datetime.datetime.now()
        print(f"Time for judge: {(end-start).total_seconds()}s")

    def must_refresh_status(self):
        if DEBUG:
            print("--must_refresh_status()")
        refresh = False

        if self.time_prev_refresh is not None:
            delay = (datetime.datetime.now() - self.time_prev_refresh).total_seconds()
            #print(f"--delay: {delay}")
            if delay >= self.CHECK_TIME_DELAY:
                #print(f"--delay {delay}  >= check_time_delay {self.CHECK_TIME_DELAY}")
                refresh = True
        else:
            self.time_prev_refresh = datetime.datetime.now()
            if DEBUG:
                print(f"--time_prev_refresh is None")

        if self.force_check:
            refresh = True
            self.force_check = False
            print("--Force check!")

        if self.snapshot:
            target_cell = self.__get_target_cell()
            if (self.curr_target_cell is not None) and (target_cell != self.curr_target_cell):
                # if the target is changed, reset the state
                # of motion analyzer to setup a new analysis
                if DEBUG:
                    print(
                        f"RESET TARGET: Prev Target={self.curr_target_cell}, Current Target={target_cell}")
                refresh = True
                self.motion_analyzer.reset()
                self.curr_target_cell = target_cell
        if DEBUG:
            print(f"MUST REFRESH STATUS: {refresh}")
        return refresh

    def set_status(self):
        if self.time_shoot_cooldown is None:
            self.time_shoot_cooldown = datetime.datetime.now()
            if DEBUG:
                print("SHOOTING COOLDOWN SETTED!")

        if self.time_flag_cooldown is None:
            self.time_flag_cooldown = time.time()
            if DEBUG:
                print("COOLDOWN SETTED!")

        game_status = self.retrieve_game_status()
        self.snapshot = self.map_analyzer.analyze(game_status)
        self.game_chat = self.chat_analyzer.analyze(
            self.retrieve_chat_status(game_status)
        )

        if DEBUG:
            print(f"GAME CHAT:\n{self.game_chat.__dict__}")

        if self.curr_target_cell is None:
            self.curr_target_cell = self.snapshot.xy_flag
        if DEBUG:
            enemies = [x.coord for x in self.snapshot.enemies_with_status]
            print(f"ENEMIES POSITIONS: {enemies}")
        aggr = self.__compute_aggressive()
        dang = self.__compute_flag_danger()
        ener = self.__compute_energy()
        if DEBUG:
            print(
                f"STATUS: Aggressive={aggr} - Flag danger={dang} - Energy={ener}")
        self.system.input['aggressive'] = aggr
        self.system.input['myflag_danger'] = dang
        self.system.input['energy'] = ener
        self.system.compute()

    def next_action(self):
        if not self.judged and (datetime.datetime.now()-self.start_match_time).total_seconds() > 15+random.random()*10:
            self.judged = True
            self.__perform_judge()

        if self.game_chat and self.game_chat.is_in_emergency_meeting and not self.already_accused:
            self.__perform_accuse()
            self.already_accused = True
        elif not self.game_chat.is_in_emergency_meeting:
            self.already_accused = False

        max_action = self.__get_max_action()
        if max_action == "move":
            self.snapshot.target = self.curr_target_cell
            if self.snapshot.xy_my_flag == self.snapshot.target:
                self.snapshot.target = self.__new_defense_target(
                    self.snapshot.xy_my_flag)
            self.__perform_move()

        elif max_action == "shoot":
            self.__force_check()
            self.__perform_shoot()

        elif max_action == "accuse":
            self.__force_check()
            self.__perform_accuse()
