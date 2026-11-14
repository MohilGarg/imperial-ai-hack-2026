"""Only plays premium hands, bets them hard."""
R = "23456789TJQKA"
class Agent:
    def act(self, s):
        a, b = sorted((R.index(c[0]) for c in s["hole_cards"]), reverse=True)
        prem = (a == b and a >= 8) or (a == 12 and b >= 10)
        if prem and "raise" in s["legal_actions"]:
            return {"action": "raise", "amount": s["min_raise_to"] + s["pot"]}
        if prem: return {"action": "call" if "call" in s["legal_actions"] else "check"}
        return {"action": "check" if "check" in s["legal_actions"] else "fold"}
