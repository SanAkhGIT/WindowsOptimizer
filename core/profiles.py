import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent/"profiles"

def load_profiles():
    profiles=[]
    for path in sorted(ROOT.glob("*.json")):
        try:
            data=json.loads(path.read_text(encoding="utf-8")); data["id"]=path.stem; profiles.append(data)
        except (OSError,json.JSONDecodeError):
            continue
    return profiles

def load_profile(profile_id):
    for profile in load_profiles():
        if profile["id"]==profile_id: return profile
    raise KeyError(profile_id)
