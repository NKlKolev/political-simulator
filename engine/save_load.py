import json
import os
import copy
from datetime import datetime

SAVES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "saves")


def save_game(state, slot=1):
    os.makedirs(SAVES_DIR, exist_ok=True)
    save_data = {
        "saved_at": datetime.now().isoformat(),
        "game_date": f"{state['date']['month']}/{state['date']['year']}",
        "turn": state["turn"],
        "state": copy.deepcopy(state)
    }
    path = os.path.join(SAVES_DIR, f"save_{slot:03d}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)
    return path


def load_game(slot=1):
    path = os.path.join(SAVES_DIR, f"save_{slot:03d}.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        save_data = json.load(f)
    return save_data["state"]


def list_saves():
    os.makedirs(SAVES_DIR, exist_ok=True)
    saves = []
    for filename in sorted(os.listdir(SAVES_DIR)):
        if filename.startswith("save_") and filename.endswith(".json"):
            path = os.path.join(SAVES_DIR, filename)
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                slot = int(filename.replace("save_", "").replace(".json", ""))
                saves.append({
                    "slot": slot,
                    "saved_at": data.get("saved_at", "Unknown"),
                    "game_date": data.get("game_date", "Unknown"),
                    "turn": data.get("turn", 0),
                    "path": path
                })
            except Exception:
                pass
    return saves


def delete_save(slot):
    path = os.path.join(SAVES_DIR, f"save_{slot:03d}.json")
    if os.path.exists(path):
        os.remove(path)
        return True
    return False
