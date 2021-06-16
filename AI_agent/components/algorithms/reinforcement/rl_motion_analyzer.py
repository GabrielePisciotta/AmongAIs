import os
import sys
import numpy as np
if __name__ == "__main__":
    ROOT_DIR = os.path.dirname(os.path.abspath("../../"))
    sys.path.append(ROOT_DIR)
    print('@', ROOT_DIR)
    from components.components import MotionAnalyzerInterface
    from config import *
else:
    sys.path.append('..')
    from components.components import MotionAnalyzerInterface
    from config import *
import operator
import random


class QLearnerMotionAnalyzer(MotionAnalyzerInterface):
    """Motion Analyzer based on Q-Learning (Off-policy TD learning) algorithm.
    """

    def __init__(self, lr=0.01, num_episodes=50, epsilon=0.3, epsilon_decay=0.00005, gamma=0.95, max_iters=1000000):
        self.actions = ["N", "S", "W", "E"]
        self.num_actions = len(self.actions)
        self.lr = lr
        self.num_episodes = num_episodes
        self.epsilon = epsilon  # threshold
        self.epsilon_decay = epsilon_decay
        self.gamma = gamma
        self.Q = None  # state-action matrix
        self.size = 0
        self.max_iters = max_iters
        self.trained = False
        self.curr_state = None

    def __init_states(self, snapshot):
        """Initialize the states list and the Q-values.
        """
        map = snapshot.map
        xy_my_flag = snapshot.xy_my_flag
        self.size = snapshot.map_size
        self.Q = {}
        for row, rows in enumerate(map):
            for col, _ in enumerate(rows):
                state = (row, col)
                self.Q[state] = {}
                if (row > 0) and (map[row-1][col] not in ["#", '@', '&', '!']) and ((row-1, col) != xy_my_flag):
                    self.Q[state]["N"] = .0
                if (row < self.size-1) and (map[row+1][col] not in ["#", '@', '&', '!']) and ((row+1, col) != xy_my_flag):
                    self.Q[state]["S"] = .0
                if (col > 0) and (map[row][col-1] not in ["#", '@', '&', '!']) and ((row, col-1) != xy_my_flag):
                    self.Q[state]["W"] = .0
                if (col < self.size-1) and (map[row][col+1] not in ["#", '@', '&', '!']) and ((row, col+1) != xy_my_flag):
                    self.Q[state]["E"] = .0

    def __greedy(self, state, eps):
        """Epsilon greedy policy for exploration & exploitation.

        Parameters
        ----------
        state : (int,int)
            the state row and col
        eps : float
            the epsilon greedy parameter

        Returns
        -------
        str
            the next action
        """
        if np.random.uniform(0, 1) < eps:
            return random.choice(list(self.Q[state]))
        else:
            return max(self.Q[state].items(), key=operator.itemgetter(1))[0]

    def __step(self, snapshot, state, action):
        """Make one step forward in the environment.

        Parameters
        ----------
        snapshot : entity.Snapshot
            the snapshot of the game
        state : (int,int)
            the current state
        action : str
            the string of the action

        Returns
        -------
        (int,int)
            the next state
        int
            the reward
        bool
            True if the state is final state, False otherwise
        """
        map, target = snapshot.map, snapshot.target
        # computing step
        next_state = None
        row, col = state[0], state[1]
        if action == "N":
            next_state = (row-1, col)
        elif action == "S":
            next_state = (row+1, col)
        elif action == "W":
            next_state = (row, col-1)
        elif action == "E":
            next_state = (row, col+1)
        # computing reward
        reward = -5
        done = False
        nxt_row, nxt_col = next_state[0], next_state[1]
        if state == target:
            reward = 5
            done = True
        elif map[nxt_row][nxt_col] in ["$"]:
            reward = -1
        return next_state, reward, done

    def __update_curr_state(self, action):
        if action == "N":
            self.curr_state = (self.curr_state[0]-1, self.curr_state[1])
        elif action == "S":
            self.curr_state = (self.curr_state[0]+1, self.curr_state[1])
        elif action == "W":
            self.curr_state = (self.curr_state[0], self.curr_state[1]-1)
        elif action == "E":
            self.curr_state = (self.curr_state[0], self.curr_state[1]+1)

    def reset(self):
        self.trained = False
        self.Q = None

    def analyze(self, snapshot=None):
        if snapshot is not None:
            map, start_state = snapshot.map, snapshot.xy_me
            self.curr_state = start_state
            if not self.trained:
                self.trained = True
                self.__init_states(snapshot)

                games_reward = [0]
                eps = self.epsilon
                for ep in range(self.num_episodes):
                    state = start_state
                    done = False
                    tot_reward = 0
                    if eps > 0.01:
                        eps -= self.epsilon_decay
                    i = 0
                    while not done and (i < self.max_iters-1):
                        action = self.__greedy(state, eps)
                        next_state, reward, done = self.__step(
                            snapshot, state, action)
                        # Bellman equation
                        max_next_qvalue = max(
                            self.Q[next_state].items(), key=operator.itemgetter(1))[1]
                        self.Q[state][action] = self.Q[state][action] + self.lr * \
                            (reward + self.gamma *
                             max_next_qvalue - self.Q[state][action])

                        state = next_state
                        tot_reward += reward
                        i += 1
                        if done:
                            games_reward.append(tot_reward)
                    if DEBUG:
                        print(
                            f"[Episode: {ep+1}/{self.num_episodes}] Iters: {i+1} - Reward: {games_reward[-1]} - Epsilon: {eps}")
        best_action = max(self.Q[self.curr_state].items(),
                          key=operator.itemgetter(1))[0]
        if DEBUG:
            print(f"BEST ACTION: {best_action} {self.Q[self.curr_state]}")
        self.__update_curr_state(best_action)
        return best_action
