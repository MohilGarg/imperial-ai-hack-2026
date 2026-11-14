import random
class Agent:
    def act(self, state):
        legal = state["legal_actions"]
        ranks = sorted("23456789TJQKA".index(c[0]) for c in state["hole_cards"])
        strong = ranks[0] == ranks[1] or ranks[1] >= 11
        if strong and "raise" in legal:
            return {"action": "raise", "amount": min(state["min_raise_to"] + state["pot"] // 2, state["max_raise_to"])}
        if "check" in legal: return {"action": "check"}
        if state["to_call"] <= state["big_blind"] * 2 or strong: return {"action": "call"}
        return {"action": "fold"}
