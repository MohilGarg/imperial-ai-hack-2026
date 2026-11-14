"""Raises or shoves most hands."""
import random
class Agent:
    def __init__(self): self.r = random.Random()
    def act(self, s):
        if "raise" in s["legal_actions"] and self.r.random() < 0.7:
            if self.r.random() < 0.25: return {"action": "all_in"}
            return {"action": "raise", "amount": s["min_raise_to"] + s["pot"]}
        return {"action": "call" if "call" in s["legal_actions"] else "check"}
