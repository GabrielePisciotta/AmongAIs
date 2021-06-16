from components.chat_handler import ChatHandler
from config import *
import time

gameserver = " ‌@GameServer"
noone = "no_one"

channel = SERVER_GAME_NAME

# trying to confuse players with "Game finished!"
chat_handler = ChatHandler(gameserver)
time.sleep(2)
print(chat_handler.send_command(f"JOIN {channel}"))
time.sleep(2)
print(chat_handler.send_command(f"POST {channel} Game finished!"))
time.sleep(2)
# trying to miscount the emergency meetings active
print(chat_handler.send_command(f"POST {channel} {START_EMERGENCY_MEETING} {noone}"))
time.sleep(2)

# trying to confuse players with "Game finished!"
chat_handler2 = ChatHandler(noone)
time.sleep(2)
print(chat_handler2.send_command(f"JOIN {channel}"))
time.sleep(2)
print(chat_handler2.send_command(f"POST {channel} @GameServer Game finished!"))
time.sleep(2)

# trying to miscount the emergency meetings active
print(chat_handler2.send_command(f"POST {channel} @GameServer {START_EMERGENCY_MEETING} {noone}"))
time.sleep(2)
