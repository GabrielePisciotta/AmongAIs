import uuid

DEBUG = True
LOGGING_ON = True

##################
# Network Manager
##################
SERVER_HOST = "margot.di.unipi.it"
SERVER_PORT = 8421
SERVER_TIMEOUT = 100
SERVER_DELAY_SEC = 0.50
TRAINING = False
if TRAINING:
    SERVER_DELAY_SEC_AFTER_JOIN = 0.05
else:
    SERVER_DELAY_SEC_AFTER_JOIN = 0.30

SERVER_NOP_MILLISEC = 40000
SERVER_NOP_SEC = 20
SERVER_GAME_NAME = "ritirati"
#SERVER_GAME_NAME = "AI7-Game-" + str(uuid.uuid4())[:5]
CMD_REQUEST_TIMEOUT_SEC = 60
CONNECTION_CLOSED = "Connection closed by remote host"
MAX_RESEND = 3
SINGLE_AGENT_MODE = False

##################
# Chat Handler
##################
CHAT_SERVER_PORT = 8422
CHAT_SERVER_NOP_SEC = 250
GLOBAL_CH = "#GLOBAL"
CHAT_CH = "#CHAT"
LEAGUE_CH = "#LEAGUE"
LOGS_CH = "#LOGS"
DATA_CH = "#DATA"
STREAM_CH = "#STREAM"
NOP_CH = "#NOP"

##################
# Chat Analyzer
##################
HIT = "hit"
START_EMERGENCY_MEETING = 'EMERGENCY MEETING! Called by'
END_EMERGENCY_MEETING = 'EMERGENCY MEETING ended'
ACCUSES = "accuses"

#################
# Printing stuff
#################
PRINT_ASCII_MAP = False
PRINT_GRAPH_PATH = True

#################
# Default agent for test game
#################
DEFAULT_AGENT = "graph"
#DEFAULT_AGENT = "rl"


################
# Test game
################
USER_INFO = "AI_7"
"""
AGENTS = []
for i in range(0, 12):
    AGENTS.append([f'AI_fab_{i}', 'fuzzy'])
"""

AGENTS = [
    ["Gandalf", "fuzzy"],
    ["DArtagnan", "fuzzy"],
    ["AlessandroMagno", "fuzzy"]
]

SINGLE_AGENT = ['Franz', 'fuzzy']

SHOOT_COOLDOWN_SEC = 5
FLAG_COOLDOWN_SEC = 30

#################################
# FLAG DANGER RADIUS PARAMETERS #
# ###############################
SMALL_FLAG_RADIUS_Q = 5
SMALL_FLAG_RADIUS_W = 10
MEDIUM_FLAG_RADIUS_Q = 15
MEDIUM_FLAG_RADIUS_W = 20
BIG_FLAG_RADIUS_Q = 25
BIG_FLAG_RADIUS_W = 30
