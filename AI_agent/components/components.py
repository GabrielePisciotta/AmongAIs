import os
import abc
import sys
import pygame
import numpy as np
import networkx as nx
import re

if __name__ != "__main__":
    from config import *
    from .entity import *


class MapAnalyzer(object):

    def __init__(self):
        self.me_symbol = None
        self.current_position = None

    def analyze(self, status):
        self.status = status
        self.my_energy = status.me.energy
        if self.me_symbol == None:
            self.me_symbol = self.status.me.symbol

        self.map = np.full(
            (self.status.rows, self.status.cols), [''], dtype=str)

        self.terrain = np.full(
            (self.status.rows, self.status.cols), ['.'], dtype=str)


        for x_pos, line in enumerate(self.status.map):
            for y_pos, cell in enumerate(line):

                if cell != "":
                    self.map[x_pos][y_pos] = cell

                    # Check if it's me
                    if self.isMe(cell):
                        self.current_position = (x_pos, y_pos)
                        self.cell_me = self.terrain[x_pos][y_pos]

                    elif cell.isalpha() and self.isFlagToConquer(cell):
                        self.flag_position = (x_pos, y_pos)

                    elif cell.isalpha() and self.isMyFlag(cell):
                        self.my_flag_position = (x_pos, y_pos)

                    elif not cell.isalpha():
                        self.terrain[x_pos][y_pos] = cell
                    """elif cell.isalpha() and (cell != status.me.symbol):
                        if cell.islower() == status.me.symbol.islower():
                            self.xy_players_allies.append((x_pos, y_pos))
                        else:
                            self.xy_players_enemies.append((x_pos, y_pos))"""

        self.current_position  = status.me.coord

        self.map = np.array(self.map)
        self.xy_players_allies = []
        self.xy_players_enemies = []
        self.enemies_status = []
        enemies_with_status = []
        allies_with_status = []

        for p in status.players:
            if p.team != status.me.team:
                self.xy_players_enemies.append(p.coord)
                enemies_with_status.append(p)
            else:
                if p.team == status.me.team:
                    self.xy_players_allies.append(p.coord)
                    allies_with_status.append(p)



        if PRINT_ASCII_MAP:
            print(self.map)

        return Snapshot(
            map=self.map,
            map_size=int(status.size),
            me_symbol=status.me.symbol,
            xy_me=self.current_position,
            cell_me=self.cell_me,
            xy_flag=self.flag_position,
            xy_my_flag=self.my_flag_position,
            xy_players_allies=self.xy_players_allies,
            xy_players_enemies=self.xy_players_enemies,
            loyalty=self.status.me.loyalty,
            target=self.flag_position,
            energy=int(self.my_energy),
            enemies_with_status=enemies_with_status,
            allies_with_status=allies_with_status
        )

    def get_map(self):
        if self.map is not None:
            return self.map
        else:
            print("No map analyzed")
            return None

    def get_current_position(self):
        return self.current_position

    def get_flag_position(self):
        return self.flag_position

    def get_element_at_position(self, position):
        """

        :param position: (x, y) coord in the map
        :return: the corresponding value
        """

        if position != None:
            return self.map[position[0]][position[1]]

    #############################
    # Type of terrain
    #############################
    def isBonus(self, cell):
        return cell == "$"

    def isRiver(self, cell):
        return cell == "~"

    def isWall(self, cell):
        return cell == "#"

    def isGrass(self, cell):
        return cell == "."

    def isOcean(self, cell):
        return cell == "@"

    def isTrap(self, cell):
        return cell == "!"

    def isBarrier(self, cell):
        return cell == "&"

    def isWalkable(self, cell):
        if self.isBonus(cell) or self.isRiver(cell) or self.isGrass(cell) or self.isTrap(cell):
            if not self.isMyFlag(cell):
                return True
        else:
            return False

    ###########################
    # Rules
    ###########################

    def isPlayer(self, cell):
        list_of_players = [p.symbol for p in self.status.players]
        return cell in list_of_players

    def isTeamMate(self, cell):
        for player in self.status.players:
            if player.symbol == cell:
                return player.team == self.status.me.team

    def isFlagToConquer(self, cell):
        if self.me_symbol.isupper():
            to_take = 'x'
        else:
            to_take = 'X'
        return cell.isalpha() and cell.isalpha() and cell == to_take

    def isMyFlag(self, cell):
        if self.me_symbol.isupper():
            to_take = 'X'
        else:
            to_take = 'x'
        return cell.isalpha() and cell.isalpha() and cell == to_take

    def isMe(self, cell):
        return cell.isalpha() and cell == self.me_symbol

    def isEnemy(self, cell):
        return cell.isalpha()


class ChatAnalyzerInterface(abc.ABC):

    @abc.abstractmethod
    def analyze(self, chat):
        """Analyze the chat.

        Parameters
        ----------
        chat : entity.GameChat
            the chat status

        Returns
        -------
        entity.ChatAnalyze
            the chat analysis.
        """
        pass


class ShootAnalyzerInterface(abc.ABC):

    @abc.abstractmethod
    def analyze(self, snapshot):
        """Analyze the status of the game to know if it can shot in a direction.

        Parameters
        ----------
        snapshot : entity.Snapshot
            the status of the game.

        Returns
        -------
        str
            the direction in which we will shoot
        """
        pass

    @abc.abstractmethod
    def is_shootable(self, snapshot, player):
        """Check if a player is shootable.

        Parameters
        ----------
        snapshot : entity.Snapshot
            the snapshot of the game
        player : entity.GamePlayer
            the player

        Returns
        -------
        bool
            True if player is shootable, False otherwise
        """
        pass

    @abc.abstractmethod
    def get_shootable_cells(self, snapshot):
        """Get shootable players.

        Parameters
        ----------
        snapshot : entity.Snapshot

        Returns
        -------
        dict(tuple,direction)
            the players coordinate and the direction on which thay are located.
        """
        pass


class MotionAnalyzerInterface(abc.ABC):

    @abc.abstractmethod
    def reset(self):
        """Reset the state.
        """
        pass

    @abc.abstractmethod
    def analyze(self, snapshot):
        """Analyze the status of the game.

        Parameters
        ----------
        snapshot : entity.Snapshot (None if no training needed)
            the status of the game.

        Returns
        -------
        str
            the action to do.
        """
        pass


class ImpostorAnalyzerInterface(abc.ABC):

    @abc.abstractmethod
    def analyze(self, snapshot, chat_analysis):
        """Find the impostor.

        Parameters
        ----------
        snapshot : [entity.Snapshot]
            the snapshot of the game
        chat_analysis : entity.ChatAnalysis
            the analysis of the chat.

        Returns
        -------
        entity.GamePlayer
            the impostor.
        """
        pass

import datetime
from scipy.spatial.distance import cityblock
class ActionManagerInterface(abc.ABC):

    def __init__(self,
                 shoot_analyzer=None,
                 motion_analyzer=None,
                 map_analyzer=None,
                 impostor_analyzer=None,
                 network_manager=None,
                 chat_handler=None,
                 chat_analyzer=None,
                 radius=5):
        self.shoot_analyzer = shoot_analyzer
        self.motion_analyzer = motion_analyzer
        self.map_analyzer = map_analyzer
        self.impostor_analyzer = impostor_analyzer
        self.network_manager = network_manager
        self.chat_handler = chat_handler
        self.chat_analyzer = chat_analyzer
        self.game_status = None
        self.chat_status = None
        self.FLAG_DANGER_RADIUS = radius
        self.already_retrieved_map = None
        self.time_prev_refresh = None
        self.old_players = {}
        self.me_symbol = None

    def retrieve_game_status(self):
        now = datetime.datetime.now()

        if self.time_prev_refresh is not None:
            elapsed = (self.time_prev_refresh - now).total_seconds()
            possible_moves = elapsed/SERVER_DELAY_SEC_AFTER_JOIN

        self.time_prev_refresh = datetime.datetime.now()

        """Retrieve game informations (Game state, players and current agent infos).
        """
        if self.already_retrieved_map is None:
            map = self.network_manager.send_command(f"{SERVER_GAME_NAME} LOOK")
            if map.split()[0] != "OK":
                print("Cannot retrieve map")
                exit()
            map = "\n".join(map.split("\n")[1:])  # Removing the first line "OK"
            map = re.sub(r"[^.xX#&!$~@|/\n]", ".", map)  # replaces everything that is not a flag
            map = [list(line) for line in map.splitlines()]
            self.already_retrieved_map = map

        else:
            map = self.already_retrieved_map


        n_rows = len(map)
        n_cols = len(map[0])

        status_res = self.network_manager.send_command(
            f"{SERVER_GAME_NAME} STATUS")
        if DEBUG:
            print(f"GAME STATUS: {status_res}")
        lines = status_res.split("\n")
        name = ""
        state = ""
        size = 0
        ratio = 'Q'
        me = None
        players = []

        count_player = 0
        for idx, line in enumerate(lines):
            if idx != 0 and line:
                if line.startswith('GA:'):
                    fields = line.split(" ")
                    name = fields[1].split("=")[1]
                    state = fields[2].split("=")[1]
                    size = fields[3].split("=")[1]
                    ratio = fields[4].split("=")[1]
                elif line.startswith('ME:'):
                    fields = line.split(" ")

                    me = GamePlayer(
                        symbol=fields[1].split("=")[1],
                        name=fields[2].split("=")[1],
                        team=int(fields[3].split("=")[1]),
                        loyalty=int(fields[4].split("=")[1]),
                        energy=int(fields[5].split("=")[1]),
                        score=int(fields[6].split("=")[1]),
                    )
                    self.me_symbol = me.symbol
                elif line.startswith('PL:'):
                    fields = line.split(" ")


                    player_coord = (int(fields[5].split("=")[1]),
                               int(fields[4].split("=")[1]))
                    player_name = fields[2].split("=")[1]

                    if me is not None:
                        if me.name == player_name:
                            me.coord = player_coord

                    active = fields[6].split("=")[1]
                    if player_name in self.old_players:
                        try:
                            speed_list = self.old_players[player_name].speed
                            if active == 'ACTIVE':
                                speed_list.append(np.abs(cityblock(self.old_players[player_name].coord, player_coord)/possible_moves))
                        except:
                            print("count_player: ", count_player)
                            print("Speed_list: ", speed_list)
                            print("self.old_players[player_name]: ", self.old_players[player_name])
                    else:
                        speed_list = []

                    pl = GamePlayer(
                        symbol=fields[1].split("=")[1],
                        name=player_name,
                        team=int(fields[3].split("=")[1]),
                        coord=player_coord,
                        active=active,
                        speed=speed_list
                    )

                    self.old_players[pl.name] = pl

                    map[pl.coord[0]][pl.coord[1]] = pl.symbol

                    if pl.symbol != self.me_symbol:
                        players.append(pl)
                    count_player += 1

        self.game_status = GameStatus(
            name=name,
            state=state,
            size=size,
            map=map,
            me=me,
            players=players,
            ratio=ratio,
            rows=n_rows,
            cols=n_cols
        )
        return self.game_status

    def retrieve_chat_status(self, game_status):
        """Retrieve chat messages and game informations.
        """
        chat = self.chat_handler.messages
        self.chat_status = GameChat(
            messages=chat,
            name=game_status.name,
            state=game_status.state,
            size=game_status.size,
            map=game_status.map,
            me=game_status.me,
            players=game_status.players
        )
        return self.chat_status

    @abc.abstractmethod
    def must_refresh_status(self):
        """Check if the status must be refreshed.

        Returns
        -------
        bool
            True if the status must be refreshed, False otherwise
        """
        pass

    @abc.abstractmethod
    def set_status(self):
        """Set the current status.
        """
        pass

    @abc.abstractmethod
    def next_action(self):
        """Performs the next action.
        """
        pass
