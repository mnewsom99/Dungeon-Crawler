
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
            
            # Post-Rescue / Town Dialogue (State handled by code switching nodes usually, or we check location)
            "town_start": {
                "text": "It feels so good to happen the sun again! Thank you for saving me. My shop is open if you need herbs.",
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
                "text": "Welcome to the Ironhand Smithy! Best steel in the region.",
                "options": [
                    {"label": "Can you upgrade my gear?", "next": "shop_info"},
                    {"label": "See you later.", "next": "end"}
                ]
            },
            "shop_info": {
                "text": "I can sell you armor and weapons. If you find Iron Ore, bring it here!",
                "options": [
                    {"label": "I'll look for ore.", "next": "end"},
                    {"label": "I found some Iron Ore!", "next": "turn_in_ore", "req_item": "Iron Ore", "action": "give_ore"}
                ]
            },
            "turn_in_ore": {
                "text": "Ah! Using the old ways, I see. Fine quality. Here is 50 gold for your trouble.",
                "options": [
                    {"label": "Show me your wares.", "next": "shop_info"},
                    {"label": "Goodbye.", "next": "end"}
                ]
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
                "text": "She is the town herbalist, but she has studied the ancient layouts. She was dragged deeper in. Please, you must save her first if you want any of us to survive.",
                "options": [
                    {"label": "I will find her.", "next": "leave"}
                ]
            },
            "leave": {
                "text": "Good luck. I will try to disrupt the magical wards from here while you search. Go!",
                "options": [
                    {"label": "Actually, follow me. We stick together.", "next": "following", "action": "follow_me"},
                    {"label": "Stay here and wait.", "next": "waiting", "action": "stay_here"}
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
                "text": "Ah, the mana flow is much more stable here. Welcome to my shop!",
                "options": [
                    {"label": "Do you have potions?", "next": "shop_info"},
                    {"label": "Bye.", "next": "end"}
                ]
            },
            "shop_info": {
                "text": "Potions, elixirs, and mysteries! Bring me Mystic Herbs and I will brew wonders.",
                "options": [
                    {"label": "Understood.", "next": "end"},
                    {"label": "I found Mystic Herbs!", "next": "turn_in_herb", "req_item": "Mystic Herb", "action": "give_herb"}
                ]
            },
            "turn_in_herb": {
                "text": "Marvelous! The essence is strong with this one. Here, take 30 gold.",
                "options": [
                    {"label": "Do you have potions?", "next": "shop_info"},
                    {"label": "Goodbye.", "next": "end"}
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
                 "text": "Greetings, hero. The village of Oakhaven has suffered greatly.",
                 "options": [
                     {"label": "How can I help?", "next": "help"},
                     {"label": "Who are you?", "next": "intro"}
                 ]
             },
             "intro": {
                 "text": "I am Elder Aethelgard. I watch over this town... or what's left of it.",
                 "options": [
                     {"label": "How can I help?", "next": "help"}
                 ]
             },
             "help": {
                 "text": "My niece Elara, Gareth the Blacksmith, and Seraphina... they were all taken to the dungeon below. Please, bring them back.",
                 "options": [
                     {"label": "I will save them.", "next": "end"}
                 ]
             },
             "end": {
                 "text": "The gods bless you.",
                 "options": []
             }
        }
    }
}
