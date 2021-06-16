import os
import sys
ROOT_DIR = os.path.dirname(os.path.abspath("../../"))
sys.path.append(ROOT_DIR)

from components.components import MotionAnalyzerInterface
from config import *
from components.entity import *

from pathlib import Path
import networkx as nx
import numpy as np
from matplotlib import transforms
import matplotlib.pyplot as plt
import random


class GraphMotionAnalyzer(MotionAnalyzerInterface):
    def __init__(self, name):
        self.agent_name = name
        self.moves = []
        self.trained = False

    def reset(self):
        self.trained = False
        self.moves = []

    def analyze(self, snapshot=None):
        if self.trained == False and snapshot or snapshot and len(self.moves) == 0:
            self.trained = True
            self.snapshot = snapshot

            current_position = snapshot.xy_me
            dest_position = snapshot.target

            # Extract the graph from the map
            self._extract_graph_from_map(snapshot.map)

            # In this list we store the next moves that the agent will do
            self.moves = []

            # Initialize with the current position
            c_p = current_position

            # For each coordinate that goes to the flag...
            for position in  self._next_moves(current_position, dest_position):
                # Add the next direction to the list
                delta = (position[0] - c_p[0], position[1] - c_p[1])
                if delta == (1, 0):
                    self.moves.append('S')
                elif delta == (-1, 0):
                    self.moves.append('N')
                elif delta == (0, -1):
                    self.moves.append('W')
                elif delta == (0, 1):
                    self.moves.append('E')

                # Update the position, in order to pretend to "have walked in the next cell"
                c_p = position

        # Return the next move
        if len(self.moves):
            m = self.moves.pop(0)
            if DEBUG:
                print(f"Prossima mossa è {m}")
            return m
        else:
            print(f"Qui per qualche motivo restituisce None")
            print(f"Path è: {self.moves}")
            return None


    def _next_moves(self, current_position, dest_position):
        if current_position == dest_position:
            return []
        try:
            path = self._get_path(current_position, dest_position)
            if DEBUG:
                print(f"Il path è: {path}")
        except Exception as e:
            print(f"Eccezione in _next_moves! Sto in {current_position}, dovrei andare in {dest_position} ma {e}")
            return [x for x in self.G.neighbors([current_position]) if self.isWalkable(x)][0]
        return path

    def _get_path(self, current_position, dest_position):
        try:
            path = nx.astar_path(self.G, source=current_position, target=dest_position, weight='weight')
            print("Ricalcolo path!")
            if PRINT_GRAPH_PATH:
                self.draw_graph(current_position, path)
            return path
        except Exception as e:
            print(f"Eccezione in _get_path! Sto in {current_position}, dovrei andare in {dest_position} ma {e} ")
            x, y = current_position
            return [random.choice([(x+1, y), (x, y+1), (x-1, y), (x, y-1)])]

    def _extract_graph_from_map(self, map: np.array) -> nx.Graph:
        self.G = nx.Graph()
        Y = len(map[0])
        X = len(map)

        for x_current_cell in range(0, X):
            for y_current_cell in range(0, Y):
                cell = map[x_current_cell][y_current_cell]
                # Skip nodes that are unwalkable
                if self.isWalkable(cell) or \
                        (x_current_cell, y_current_cell) == self.snapshot.xy_me or \
                        (x_current_cell, y_current_cell) == self.snapshot.xy_flag:
                    if not (x_current_cell, y_current_cell) == self.snapshot.xy_my_flag:
                        neighbors = lambda x, y: [(v[0], v[1]) for v in [(x - 1, y), (x, y + 1), (x + 1, y), (x, y - 1)]
                                                  if (-1 < x <= X and
                                                      -1 < y <= Y and
                                                      (x != v[0] or y != v[1]) and
                                                      (0 <= v[0] < X) and
                                                      (0 <= v[1] < Y))]

                        coords = neighbors(x_current_cell, y_current_cell)

                        for neighbors_coords in coords:
                            x_neighbor_cell, y_neighbor_cell = neighbors_coords

                            """if x_neighbor_cell == 0 \
                                or y_neighbor_cell == 0 \
                                   or x_neighbor_cell == X or y_neighbor_cell == Y:
                                continue"""

                            neighbor = map[x_neighbor_cell][y_neighbor_cell]

                            if self.isBonus(neighbor):  # bonus -> accessible
                                self.G.add_edge((x_current_cell, y_current_cell), (x_neighbor_cell, y_neighbor_cell), weight=0)

                            elif self.isGrass(neighbor) or self.isRiver(neighbor):  # grass or river
                                self.G.add_edge((x_current_cell, y_current_cell), (x_neighbor_cell, y_neighbor_cell),
                                                weight=0.2)
                            elif (x_neighbor_cell, y_neighbor_cell) == self.snapshot.xy_flag:
                                self.G.add_edge((x_current_cell, y_current_cell), (x_neighbor_cell, y_neighbor_cell), weight=0)

                            elif self.isTrap(neighbor):  # trap-> walkable but not good to go through it
                                self.G.add_edge((x_current_cell, y_current_cell), (x_neighbor_cell, y_neighbor_cell), weight=1)

                            elif self.isBarrier(neighbor):
                                # the following ugly thing is in order to check if there's a neighbour of the cell with '&'
                                # in order to possibly move the barrier there. We check even if the grass cell is not the cell
                                # where we are now.
                                coords_barrier = neighbors(x_neighbor_cell, y_neighbor_cell)
                                for barrier_neighbors_coords in coords_barrier:
                                    x_barrier_neighbor_cell, y_barrier_neighbor_cell = barrier_neighbors_coords
                                    if x_barrier_neighbor_cell != x_current_cell \
                                            and y_barrier_neighbor_cell != y_current_cell \
                                            and self.isGrass(map[x_barrier_neighbor_cell][y_barrier_neighbor_cell]):
                                        self.G.add_edge((x_current_cell, y_current_cell), (x_neighbor_cell, y_neighbor_cell),
                                                        weight=0.1)

    def draw_graph(self, current_position, path):
        return
        Path(os.path.join("snapshots", self.agent_name)).mkdir(parents=True, exist_ok=True)
        f = plt.figure()
        val_map = {current_position: 1.0}
        values = [val_map.get(node, 0.25) for node in self.G.nodes()]
        edges, weights = zip(*nx.get_edge_attributes(self.G, 'weight').items())
        pos = dict((n, n) for n in self.G.nodes())
        path_edges = set(zip(path, path[1:]))
        nx.draw(self.G, pos, node_color=values, node_size=10, edgelist=edges, edge_color=weights,
                cmap=plt.get_cmap('seismic'), edge_cmap=plt.get_cmap('viridis'))
        nx.draw_networkx_nodes(self.G, pos, nodelist=path, node_color='r', node_size=5)
        nx.draw_networkx_edges(self.G, pos, edgelist=path_edges, edge_color='r')
        f.show()
        f.savefig(os.path.join('snapshots', self.agent_name, f"graph_{self.moove}.png"), format="png")

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
            return True
        else:
            return False


