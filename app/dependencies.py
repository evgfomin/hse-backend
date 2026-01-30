import json
from pathlib import Path

def save_appeals(appeal: dict):
    with Path("appeals.json").open("w", encoding="utf-8") as f:
        json.dump(appeal, f, ensure_ascii=False, indent=2)