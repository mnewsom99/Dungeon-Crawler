from dungeon.database import get_session, Player
from dungeon.quests import QuestManager

session = get_session()
player = session.query(Player).first()

if player:
    print(f"Player: {player.name}")
    print(f"Quest State Raw: {player.quest_state}")
    
    qm = QuestManager(session, player)
    print(f"Quest Status 'herbal_remedy': {qm.get_status('herbal_remedy')}")
else:
    print("No player found.")
