"""Game Entities.
"""


class GamePlayer(object):

    def __init__(self, symbol="", name="", team=0, loyalty=0, energy=0, score=0, active="ACTIVE", coord=(0, 0), speed=[]):
        self.symbol = symbol
        self.name = name
        self.team = team
        self.loyalty = loyalty
        self.energy = energy
        self.score = score
        self.active = active
        self.coord = coord
        self.speed = speed


class GameStatus(object):

    def __init__(self, name="", state="", size=0, map="", me=GamePlayer(), players=[], ratio='Q', rows=0, cols=0):
        self.name = name
        self.state = state
        self.size = size
        self.map = map
        self.me = me
        self.players = players
        self.ratio = ratio
        self.rows = rows
        self.cols = cols


class GameChat(object):

    def __init__(self, messages=[], name="", state="", size=0, map="", me=GamePlayer(), players=[]):
        self.messages = messages
        self.name = name
        self.state = state
        self.size = size
        self.map = map
        self.me = me
        self.players = players


class ChatAnalysis(object):

    def __init__(self, enemy_kills, ally_kills, is_in_emergency_meeting):
        self.enemy_kills = enemy_kills
        self.ally_kills = ally_kills
        self.is_in_emergency_meeting = is_in_emergency_meeting


class Snapshot(object):

    def __init__(self, map, map_size, me_symbol, xy_me, cell_me, xy_flag, xy_my_flag,
                 xy_players_allies, xy_players_enemies, loyalty, target, energy,
                 enemies_with_status, allies_with_status):
        self.map = map
        self.map_size = map_size
        self.me_symbol = me_symbol
        self.xy_me = xy_me
        self.cell_me = cell_me
        self.xy_flag = xy_flag
        self.xy_my_flag = xy_my_flag
        self.xy_players_allies = xy_players_allies
        self.xy_players_enemies = xy_players_enemies
        self.loyalty = loyalty
        self.target = target
        self.my_energy = energy
        self.enemies_with_status = enemies_with_status
        self.allies_with_status = allies_with_status
