from config import *
from components.components import ChatAnalyzerInterface
from components.entity import ChatAnalysis


class ChatAnalyzer(ChatAnalyzerInterface):

    def analyze(self, chat):
        """
        Perform an analysis of the chat to recollect useful informations about kills and
        emergency meetings.

        Parameters
        ----------
        chat : entity.GameChat
            the chat messages and the game status to be analyzed.

        Returns
        -------
        entity.ChatAnalysis
            the analysis of the chat.
        """

        if DEBUG:
            print(f"Messagges from Chat Analyzer ready to be processed: {chat.messages}")

        enemy_kills = {}
        ally_kills = {}
        is_in_emergency_meeting = False
        msgs = chat.messages
        n_emergency_meetings = 0
        n_end_emergency_meetings = 0

        for i, m in enumerate(msgs):

            channel = m.split()[0]
            name = m.split()[1]
            text = m.split()[2:]

            if DEBUG:
                print(f"[messaggio {i}] Name {name}")

            if name == "@GameServer":
                if DEBUG:
                    print(f"[ messaggio del GameServer ] ")
                    print(f"\t\t--> {text} <--")

                # emergency meeting analysis

                if " ".join(text).startswith(START_EMERGENCY_MEETING):
                    n_emergency_meetings += 1

                elif " ".join(text).startswith(END_EMERGENCY_MEETING):
                    n_end_emergency_meetings += 1

                if n_emergency_meetings - n_end_emergency_meetings > 0:
                    is_in_emergency_meeting = True

                if DEBUG:
                    print(
                        f"n_emergency_meetings: {n_emergency_meetings}, n_end_emergency_meetings: {n_end_emergency_meetings}, "
                        f"is_in_emergency_meeting: {is_in_emergency_meeting}")

            # kills analysis
            hit_players = [string for string in text if HIT in text and string != HIT]
            if len(hit_players) > 0:
                if DEBUG:
                    print(hit_players)
                    print(f"{hit_players[0]} shot {hit_players[1]}! Check these!")

                pl1, pl2 = None, None
                # check which player shoot other players in order to recollect statistical information about
                # the players' kills
                for pl in chat.players:
                    if hit_players[0] == pl.name:
                        pl1 = pl
                    if hit_players[1] == pl.name:
                        pl2 = pl
                if pl1 and pl2:
                    if pl1.team == pl2.team:
                        if pl1.name in ally_kills:
                            ally_kills[pl1.name] += 1
                        else:
                            ally_kills[pl1.name] = 1
                    else:
                        if pl1.name in enemy_kills:
                            enemy_kills[pl1.name] += 1
                        else:
                            enemy_kills[pl1.name] = 1

        return ChatAnalysis(enemy_kills, ally_kills, is_in_emergency_meeting)
