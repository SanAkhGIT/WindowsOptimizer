from tweaks.ui_tweaks import scan_ui_tweaks
from tweaks.personalization import scan_personalization
from modules.performance import scan as performance_scan
from modules.privacy import scan as privacy_scan
from modules.network import scan as network_scan
from modules.fixes import scan as fixes_scan

def all_tweaks(): return scan_ui_tweaks()+scan_personalization()+performance_scan()+privacy_scan()+network_scan()+fixes_scan()
