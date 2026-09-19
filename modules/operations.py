from core.models import Tweak
from modules.catalog import all_tweaks

def by_id(): return {t.id:t for t in all_tweaks()}

def profile_tweaks(ids):
    catalog=by_id(); return [catalog[i] for i in ids if i in catalog and catalog[i].apply]

def recommended_tweaks(): return [t for t in all_tweaks() if t.recommended and t.apply]
