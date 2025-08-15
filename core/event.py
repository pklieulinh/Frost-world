import random

class GameEvent:
    def __init__(self, key, data):
        self.key = key
        self.name = data.get("name", key)
        self.desc = data.get("desc", "")
        self.type = data.get("type", "normal")
        self.trigger = data.get("trigger", {})
        self.effect = data.get("effect", {})

class EventManager:
    def __init__(self, event_data):
        self.events = {k: GameEvent(k, v) for k, v in event_data.items()}
        self.event_log = []
        self.active_events = []

    def trigger(self, key, context=None):
        ev = self.events.get(key)
        if ev:
            self.event_log.append(("EVENT", ev.desc))
            self.active_events.append(ev)
            # Event Chain
            chain = ev.effect.get("event_chain", [])
            if isinstance(chain, str):
                chain = [chain]
            for chain_event in chain:
                if chain_event in self.events:
                    self.trigger(chain_event, context)

    def apply_effects(self, kingdom, parties, npcs, questboard):
        for ev in self.active_events:
            for k, v in ev.effect.items():
                if k == "morale":
                    kingdom.morale += v
                elif k == "gold":
                    kingdom.gold += v
                elif k == "fame":
                    kingdom.fame += v
                elif k == "population":
                    kingdom.population += v
                elif k == "kingdom_level":
                    kingdom.level += v
                elif k == "add_hero":
                    kingdom.spawn_hero()
                elif k == "add_quest":
                    questboard.add_random_quest()
                elif k == "quest":
                    questboard.add_quest(v)
        self.active_events = []

    def check_and_trigger(self, kingdom, parties, season, fame):
        pool = []
        for ev in self.events.values():
            trig = ev.trigger
            if trig.get("season") and trig["season"] != "any" and trig["season"] != season:
                continue
            if trig.get("fame") and fame < trig["fame"]:
                continue
            if trig.get("kingdom_level") and kingdom.level < trig["kingdom_level"]:
                continue
            pool.append(ev)
        if pool:
            ev = random.choice(pool)
            self.trigger(ev.key)