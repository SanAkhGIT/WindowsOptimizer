from pathlib import Path
from PIL import Image

ASSET_DIR = Path(__file__).resolve().parent.parent / "assets" / "generated"

def _black_image(name, size=(3840, 2160)):
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    path = ASSET_DIR / name
    if not path.exists():
        Image.new("RGB", size, (0, 0, 0)).save(path, "PNG")
    return path

def scan_personalization():
    wallpaper = _black_image("black-desktop.png")
    lock = _black_image("black-lockscreen.png")
    return [
        {"id":"black_wallpaper","name":"Pure black desktop wallpaper","description":f"Uses an application-generated #000000 wallpaper: {wallpaper.name}","risk":"SAFE","recommended":True,"path":str(wallpaper)},
        {"id":"black_lockscreen","name":"Pure black lock screen asset","description":"Generates a black lock-screen image; application will only apply supported Windows mechanisms.","risk":"SAFE","recommended":True,"path":str(lock)},
    ]

def apply_personalization(tweak):
    pass
