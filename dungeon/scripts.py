
# Dialogue Trees for NPCs
# Format:
# "NPC_Name": {
#    "start_node": "id",
#    "nodes": {
#        "id": {
#            "text": "Dialogue text...",
#            "options": [
#                {"label": "Player response", "next": "next_node_id"},
#                {"label": "Action response", "next": "next_node", "action": "function_name"}
#            ]
#        }
#    }
# }

NPC_SCRIPTS = {
    "Elara": {
        "id": "elara",
        "start_node": "start",
        "nodes": {
            "start": {
                "text": "Sshhh! Keep your voice down! The skeletons... they are everywhere. Who are you?",
                "options": [
                    {"label": "I am an adventurer. I'm here to help.", "next": "intro"},
                    {"label": "Just a wanderer. Who are you?", "next": "who"}
                ]
            },
            "who": {
                "text": "I am Elara, the herbalist from Oakhaven. They dragged me down here days ago... I haven't seen the sun since.",
                "options": [
                    {"label": "Don't worry, I'll get you out.", "next": "plan"}
                ]
            },
            "intro": {
                "text": "An adventurer? Thank the gods. I thought I was going to rot in this cell.",
                "options": [
                    {"label": "Do you know a way out?", "next": "plan"}
                ]
            },
            "plan": {
                "text": "I've been watching them. There is a loose brick on the NORTH wall. It triggers a hidden door! Please, open it and I can run to safety.",
                "options": [
                    {"label": "Stand back. I'll open it.", "next": "end_rescue", "action": "rescue_elara"}
                ]
            },
            "end_rescue": {
                "text": "Thank you! I'll meet you in Oakhaven!",
                "options": [] # End
            },
            
            # Post-Rescue / Town Dialogue
            "town_start": {
                "text": "It feels so good to see the sun again! Thank you for saving me. My shop is open if you need herbs.",
                "options": [
                    {"label": "What do you sell?", "next": "shop_info"},
                    {"label": "Goodbye.", "next": "end"}
                ]
            },
            "shop_info": {
                "text": "I sell healing poultices and magic herbs. If you find any Mystic Herbs in the dungeon, bring them to me!",
                "options": [
                    {"label": "I'll keep an eye out.", "next": "end"}
                ]
            },
            "end": {
                "text": "Safe travels, hero.",
                "options": []
            }
        }
    },

    "Gareth Ironhand": {
        "id": "gareth",
        "start_node": "start",
        "nodes": {
             "start": {
                 "text": "Hmph. About time someone showed up. You don't look like one of the Warden's lackeys.",
                 "options": [
                     {"label": "I'm here to rescue you, Gareth.", "next": "rescue_offer"},
                     {"label": "Lackey? Watch your tongue.", "next": "tough"}
                 ]
             },
             "tough": {
                 "text": "Hah! A spine! Good. I'm Gareth Ironhand. I've been stuck here refusing to forge weapons for these skeletons.",
                 "options": [
                     {"label": "Let's get you out of here.", "next": "rescue_offer"}
                 ]
             },
             "rescue_offer": {
                 "text": "Aye, I'm ready to leave. My hammer belongs in my smithy, not this damp hole.",
                 "options": [
                     {"label": "Go. The path is clear.", "next": "end_rescue", "action": "rescue_gareth"}
                 ]
             },
             "end_rescue": {
                 "text": "Right! Come see me in Oakhaven. I'll sharpen that blade of yours for free!",
                 "options": []
             },
             
             "town_start": {
                "text_dynamic": "gareth_status",
                "text": "Welcome to the Ironhand Smithy! Best steel in the region.",
                "options": [
                    {"label": "I have Iron Ore.", "next": "turn_in_ore", "action": "complete_quest:iron_supply", "req_quest_active": "iron_supply", "req_item": "Iron Ore"},
                    {"label": "I found the Titanium Fragment!", "next": "turn_in_titanium", "action": "complete_quest:titanium_hunt", "req_quest_active": "titanium_hunt", "req_item": "Titanium Fragment"},
                    {"label": "Can you upgrade my gear?", "next": "shop_info"},
                    {"label": "See you later.", "next": "end"}
                ]
            },
            "shop_info": {
                "text": "I can sell you armor and weapons. I also need supplies to keep the forge hot.",
                "options": [
                    {"label": "What do you need?", "next": "quests_check"},
                    {"label": "Goodbye", "next": "end"}
                ]
            },
            "quests_check": {
                "text": "Efficiency is key. What have you got?",
                "options": [
                    # Iron Ore Quest (Available)
                    {"label": "I can find Iron Ore.", "next": "accept_iron", "action": "accept_quest:iron_supply"},
                    
                    # Iron Ore Turn In
                    {"label": "I have Iron Ore.", "next": "turn_in_ore", "action": "complete_quest:iron_supply", "req_quest_active": "iron_supply", "req_item": "Iron Ore"},
                    
                    # Titanium Quest Offer (Req: Iron Supply Completed)
                    # Note: We rely on req_quest_complete to show this option only if iron_supply is done.
                    {"label": "Any harder work?", "next": "titanium_offer", "req_quest_complete": "iron_supply"},
                    
                    # Titanium Turn In
                    {"label": "I found the Titanium Fragment!", "next": "turn_in_titanium", "action": "complete_quest:titanium_hunt", "req_quest_active": "titanium_hunt"}
                ]
            },
            "accept_iron": {
                "text": "Good. Bring me 1 chunk of Iron Ore.",
                "options": [{"label": "On it.", "next": "end"}]
            },
            "turn_in_ore": {
                "text": "Refined quality. Here is 50 gold. If you want a real challenge, ask me again.",
                "options": [{"label": "Thanks.", "next": "shop_info"}]
            },
            "titanium_offer": {
                "text": "The Earth Dungeon to the North holds 'Titanium Fragments'. They are rare, found on rock monsters. Bring me one, and I shall forge a legend.",
                "options": [
                    {"label": "I'll find it.", "next": "end", "action": "accept_quest:titanium_hunt"},
                    {"label": "Maybe later.", "next": "end"}
                ]
            },
            "turn_in_titanium": {
                "text": "By the flames! This metal sings! Take this Titanium Greatsword as your reward.",
                "options": [{"label": "Incredible!", "next": "end"}]
            },
            "end": {
                "text": "Strike true!",
                "options": []
            }
        }
    },

    "Seraphina": {
        "id": "seraphina",
        "start_node": "start",
        "nodes": {
             "start": {
                 "text": "We are trapped in here! I've calculated the probability of escape... it's near zero without help. We need to find Elara. She knows these dungeons better than anyone and may know a way out.",
                 "options": [
                     {"label": "Who is Elara?", "next": "who_elara"},
                     {"label": "I'll find her.", "next": "leave"}
                 ]
             },
             "who_elara": {
                 "text": "She is the town herbalist, but she has studied the ancient layouts. She was dragged deeper in. Please, you must save her first.",
                 "options": [
                     {"label": "I will find her.", "next": "leave"}
                 ]
             },
             "leave": {
                 "text": "Good luck. I will try to disrupt the magical wards from here while you search. Go!",
                 "options": [
                     {"label": "Actually, follow me.", "next": "following", "action": "follow_me"},
                     {"label": "Stay here.", "next": "waiting", "action": "stay_here"}
                 ]
             },
             "following": {
                 "text": "Very well. I shall stay close. Do not lead us into a trap.",
                 "options": [
                     {"label": "Let's move.", "next": "following_loop"}
                 ]
             },
             "following_loop": {
                 "text": "I am right behind you.",
                 "options": [
                     {"label": "Wait here.", "next": "waiting", "action": "stay_here"}
                 ]
             },
             "waiting": {
                 "text": "I will remain here. Do not be long.",
                 "options": [
                     {"label": "Follow me.", "next": "following", "action": "follow_me"}
                 ]
             },
             "end_rescue": {
                 "text": "I'll head for the exit as soon as the path is clear! Thank you!",
                 "options": []
             },

             "town_start": {
                "text_dynamic": "seraphina_status",
                "text": "Welcome to my Alchemy Shop! The mana here is pristine.",
                "options": [
                    {"label": "Here are the herbs.", "next": "turn_in_herb", "action": "complete_quest:herbal_remedy", "req_quest_active": "herbal_remedy", "req_item": "Mystic Herb"},
                    {"label": "I have the Fire and Ice reagents!", "next": "turn_in_reagents", "action": "complete_quest:elemental_reagents", "req_quest_active": "elemental_reagents", "req_item": "Everburning Cinder"}, # Note: Checking one of the items here for simplicity or relying on quest engine in future
                    # Actually we need to check TWO items. Our engine likely only checks one 'req_item'.
                    # For safety, we keep the option visible but button press validates in backend?
                    # Or we rely on 'can_complete' in DialogueSystem which checks ALL objectives. 
                    # Yes, DialogueSystem.py Line 98 checks `qm.can_complete(qid)`.
                    # So "req_quest_active" ensures it only shows if active, and clicking validates items?
                    # Wait, Line 100 in dialogue.py: IF option has "complete_quest:id", it HIDES it if !can_complete.
                    # So we don't strictly need req_item for the *option to appear* if we trust can_complete.
                    
                    {"label": "Do you have potions?", "next": "shop_info"},
                    {"label": "Bye.", "next": "end"}
                ]
            },
            "shop_info": {
                "text": "Potions, elixirs, and mysteries! Bring me Mystic Herbs and I will brew wonders.",
                "options": [
                     {"label": "I can help gather.", "next": "quests_check"},
                     {"label": "Goodbye.", "next": "end"}
                ]
            },
            "quests_check": {
                "text": "Nature provides, but we must gather. What have you found?",
                "options": [
                    # Herb Quest
                    {"label": "I'll find Mystic Herbs.", "next": "accept_herb", "action": "accept_quest:herbal_remedy"},
                    {"label": "Here are the herbs.", "next": "turn_in_herb", "action": "complete_quest:herbal_remedy", "req_quest_active": "herbal_remedy"},
                    
                    # Potion Quest (Req: Herb Done)
                    {"label": "I seek powerful magic.", "next": "reagent_offer", "req_quest_complete": "herbal_remedy"},
                    {"label": "I have the Fire and Ice reagents!", "next": "turn_in_reagents", "action": "complete_quest:elemental_reagents", "req_quest_active": "elemental_reagents"}
                ]
            },
            "accept_herb": {
                "text": "Excellent. I need 1 Mystic Herb.",
                "options": [{"label": "Okay.", "next": "end"}]
            },
            "turn_in_herb": {
                "text": "Lovely aroma. Here is 30 gold. Come back if you wish to delve deeper into alchemy.",
                "options": [{"label": "Thanks.", "next": "shop_info"}]
            },
            "reagent_offer": {
                "text": "The Fire Dungeon has 'Everburning Cinders'. The Ice Dungeon has 'Freezing Spikes'. Bring me one of each, and I will brew a Potion of Power for you.",
                "options": [
                    {"label": "I accept.", "next": "end", "action": "accept_quest:elemental_reagents"}
                ]
            },
            "turn_in_reagents": {
                 "text": "Incredible! Fire and Ice... contained in glass. Here is your Potion of Power!",
                 "options": [
                     {"label": "Thank you!", "next": "end"}
                 ]
            },
            "end": {
                "text": "May the stars guide you.",
                "options": []
            }
        }
    },
    
    "Elder Aethelgard": {
        "id": "elder",
        "start_node": "start",
        "nodes": {
             "start": {
                 "text": "Greetings, hero! The village of Oakhaven is in your debt for saving my people.",
                 "options": [
                     {"label": "I'm happy to help.", "next": "quest"},
                     {"label": "Who are you?", "next": "intro"}
                 ]
             },
             "intro": {
                 "text": "I am Elder Aethelgard. Thanks to you, Gareth and Elara are safe. But a new danger looms.",
                 "options": [
                     {"label": "What danger?", "next": "quest"}
                 ]
             },
             "quest": {
                 "text": "The North Forest is blocked by four ancient Elemental Dungeons (Fire, Ice, Earth, Air). Merchants cannot reach us! If you clear the 4 bosses, I will grant you a house.",
                 "options": [
                     {"label": "I will handle it.", "next": "end_quest", "action": "accept_quest:elemental_balance"},
                     {"label": "A house?", "next": "house_info"}
                 ]
             },
             "house_info": {
                 "text": "Yes! A plot of land right here in Oakhaven. A place to rest and store your loot. But first, the roads must be safe.",
                 "options": [
                     {"label": "I'll do it.", "next": "end_quest", "action": "accept_quest:elemental_balance"}
                 ]
             },
             "end_quest": {
                  "text": "Go North, into the forest. Be careful of the beasts.",
                  "options": []
             },

             "town_start": {
                "text_dynamic": "elder_status",
                "text": "Fallback text.",
                "options": [
                    # Accept Quest (if available/failed regex check in dynamic?)
                    # We rely on 'req_quest_active' logic to show relevant options
                    
                    # 1. Quest Offer (Available) check is handled by 'status' in text, but options?
                    # The options list is static. We must provide options for ALL states and filter them.
                    
                    # IF AVAILABLE:
                    {"label": "I will handle it.", "next": "end_quest", "action": "accept_quest:elemental_balance", "req_quest_active": "none"}, # Assuming simple check
                     # Actually our filter currently only has req_quest_active (must be active) or req_quest_complete.
                     # We need "req_quest_available" or similar.
                     # For now, let's just show options and let the text guide.
                     # Or rely on "start" node for initial acceptance, and "town_start" strictly for updates?
                     # No, DialogueSystem forces town_start if in town.
                     
                     # AVAILABLE:
                     {"label": "Tell me about the danger.", "next": "quest"}, 
                     
                     # ACTIVE:
                     {"label": "I'm working on it.", "next": "end"},
                     
                     # COMPLETE (Ready to turn in - wait, we need 'can_complete' check?
                     # The quest object has 'prevent_turn_in': True. 
                     # So "complete_quest" action will fail if objectives false.
                     # But we want to show the OPTION only if objectives met.
                     # We lack "req_quest_can_complete" filter.
                     # I will add a generic "Check Reward" button that always appears if active?
                     
                     {"label": "I have defeated them all!", "next": "turn_in_elemental", "action": "complete_quest:elemental_balance", "req_quest_active": "elemental_balance"}
                ]
             },
             
             "turn_in_elemental": {
                 "text": "You have saved us all! The house deed is yours.",
                 "options": [{"label": "Thank you, Elder.", "next": "end"}]
             },

             "end": {
                 "text": "The gods bless you.",
                 "options": []
             }
        }
    }
}
