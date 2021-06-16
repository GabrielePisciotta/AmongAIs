import sys
sys.path.append('../')
from components.components import ShootAnalyzerInterface
from config import *
import numpy as np
import random

class SimpleShootAnalyzer(ShootAnalyzerInterface):

    def analyze(self, map_snapshot):
        if DEBUG:
            enemies_coords_cord = [x.coord for x in map_snapshot.enemies_with_status]
            print(f"Cell Me: {map_snapshot.cell_me}")
            print(f"Coord Me: {map_snapshot.xy_me}")
            print(f"Players enemies 1: {map_snapshot.xy_players_enemies}")
            print(f"Players enemies 2: {enemies_coords_cord}")

        if map_snapshot.cell_me == ".":
            shootable_cell = self.get_shootable_cells(map_snapshot)
            if DEBUG:
                print(f"{shootable_cell.keys()}")

            self.shootable_cell = shootable_cell

            for enemy_position in map_snapshot.enemies_with_status:
                if enemy_position.active == 'ACTIVE':
                    x, y = enemy_position.coord
                    if (x, y) in shootable_cell.keys():
                        if DEBUG:
                            print(f"Enemy position {(x,y)} is shootable")

                        return shootable_cell[(x, y)]
        return None


    def get_shootable_cells(self, map_snapshot):
        n_rows = len(map_snapshot.map)
        n_cols = len(map_snapshot.map[0])

        allies_positions =  map_snapshot.allies_with_status
        allies_positions = [x.coord for x in allies_positions]

        x, y = map_snapshot.xy_me
        shootable_cell = {}
        for x_map in range(x, n_rows):
            if map_snapshot.map[x_map][y] in ["#","&"]:
                break
            elif (x_map, y) in allies_positions:
                break
            else:
                shootable_cell[(x_map, y)] = "S"
                
        for x_map in reversed(range(0, x)):
            if map_snapshot.map[x_map][y] in ["#","&"]:
                break
            elif (x_map, y) in allies_positions:
                break
            else:
                shootable_cell[(x_map, y)] = "N"
                
        for y_map in range(y, n_cols):
            if map_snapshot.map[x][y_map] in ["#","&"]:
                break
            elif (x, y_map) in allies_positions:
                break
            else:
                shootable_cell[(x, y_map)] = "E"
                
        for y_map in reversed(range(0, y)):
            if map_snapshot.map[x][y_map] in ["#","&"]:
                break
            elif (x, y_map) in allies_positions:
                break
            else:
                shootable_cell[(x, y_map)] = "W"
        
        return shootable_cell

    def is_shootable(self, snapshot, player):
        is_active = player.active == 'ACTIVE'
        self.shootable_cell = self.get_shootable_cells(snapshot)

        if is_active:
            enemy_row, enemy_col = player.coord
            if (enemy_row, enemy_col) in self.shootable_cell:

                if DEBUG:
                    print(f"({snapshot.me_symbol})I'm in {snapshot.xy_me}, PLAYER {player.symbol} is SHOOTABLE {player.__dict__}")
                return True
            else:
                return False
        else:
            return False