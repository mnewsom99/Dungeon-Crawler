import ollama

class AIBridge:
    def __init__(self, model="llama3"):
        self.model = model
        # Base personas - eventually load from DB for NPCs
        self.personas = {
            "dm": "You are the Dungeon Master for a dark fantasy RPG. Describe the current room or situation vividly but briefly (max 2 sentences). Focus on sensory details (lighting, smells, sounds). Do not ask the player what they want to do, just describe.",
            "combat": "You are narrating a combat action. Be visceral and punchy. Describe the impact of the blow. Use present tense.",
            "brogun": "You are Brogun, a grumpy Irish Dwarf Blacksmith. You sell weapons and armor. You are impatient but skilled. You hate elves.",
            "dredge": "You are Dredge, the Tavern Keeper of The Rusty Tankard. You are weary, cynical, and speak in a low rumble. You sell rumors and ale."
        }

    def chat(self, user_input, persona="dm", context=None):
        """
        Send a chat to the LLM with a specific persona.
        args:
            user_input (str): The prompt or player's message.
            persona (str): Key for the system prompt instructions.
            context (str): Optional game state injection (e.g., "Player has 5 HP").
        """
        system = self.personas.get(persona, self.personas["dm"])
        
        messages = [
            {'role': 'system', 'content': system}
        ]
        
        if context:
            messages.append({'role': 'system', 'content': f"[GAME CONTEXT]: {context}"})
            
        messages.append({'role': 'user', 'content': user_input})
        
        try:
            # print(f"AIBridge: Generating response for '{persona}'...")
            # Simple fallback for now if connection is flaky
            import requests
            
            # Manual call to Ollama with timeout
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False
            }
            
            # 5 Second Timeout to prevent UI lockup
            response = requests.post("http://localhost:11434/api/chat", json=payload, timeout=5)
            response.raise_for_status()
            res = response.json()
            return res['message']['content']
            
        except Exception as e:
            print(f"AIBridge Error: {e}")
            # Fallback responses based on persona
            if persona == "npc":
                return "..."
            return "The shadows are too deep to see clearly."
