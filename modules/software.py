from dataclasses import dataclass
from typing import Iterable
import re
from core.process import run_executable

@dataclass(frozen=True)
class AppSpec:
    id: str
    name: str
    category: str
    description: str
    source: str = "winget"
    foss: bool = False

CATALOG = [
    AppSpec("Google.Chrome","Google Chrome","Browsers","Fast Chromium browser."),
    AppSpec("Mozilla.Firefox","Mozilla Firefox","Browsers","Open-source browser with strong customization.",foss=True),
    AppSpec("Microsoft.Edge","Microsoft Edge","Browsers","Microsoft's Chromium-based browser."),
    AppSpec("Brave.Brave","Brave","Browsers","Chromium browser with built-in privacy features."),
    AppSpec("7zip.7zip","7-Zip","Utilities","Open-source file archiver.",foss=True),
    AppSpec("voidtools.Everything","Everything","Utilities","Fast file-name search utility."),
    AppSpec("Microsoft.PowerToys","PowerToys","Utilities","Microsoft utilities for Windows power users."),
    AppSpec("WinSCP.WinSCP","WinSCP","Utilities","SFTP, FTP and SCP file transfer client."),
    AppSpec("ShareX.ShareX","ShareX","Utilities","Open-source screenshot and capture utility.",foss=True),
    AppSpec("File-New-Project.EarTrumpet","EarTrumpet","Utilities","Per-app audio controls for Windows.",foss=True),
    AppSpec("Bitwarden.Bitwarden","Bitwarden","Security","Open-source password manager.",foss=True),
    AppSpec("VideoLAN.VLC","VLC","Media","Open-source media player.",foss=True),
    AppSpec("Spotify.Spotify","Spotify","Media","Music and podcast desktop app."),
    AppSpec("OBSProject.OBSStudio","OBS Studio","Media","Open-source recording and streaming software.",foss=True),
    AppSpec("HandBrake.HandBrake","HandBrake","Media","Open-source video transcoder.",foss=True),
    AppSpec("qBittorrent.qBittorrent","qBittorrent","Media","Open-source BitTorrent client.",foss=True),
    AppSpec("Discord.Discord","Discord","Communication","Voice, video and community chat."),
    AppSpec("Telegram.TelegramDesktop","Telegram","Communication","Desktop Telegram client."),
    AppSpec("Valve.Steam","Steam","Gaming","PC game store and launcher."),
    AppSpec("EpicGames.EpicGamesLauncher","Epic Games Launcher","Gaming","Epic Games launcher."),
    AppSpec("GOG.Galaxy","GOG Galaxy","Gaming","GOG game library and launcher."),
    AppSpec("Notepad++.Notepad++","Notepad++","Development","Open-source advanced text editor.",foss=True),
    AppSpec("Microsoft.VisualStudioCode","Visual Studio Code","Development","Extensible source-code editor."),
    AppSpec("Git.Git","Git","Development","Distributed version-control system.",foss=True),
    AppSpec("Python.Python.3","Python 3","Development","Python runtime for development and automation.",foss=True),
    AppSpec("Microsoft.PowerShell","PowerShell","Development","Modern PowerShell."),
    AppSpec("Microsoft.WindowsTerminal","Windows Terminal","Development","Modern terminal host for Windows.",foss=True),
    AppSpec("WinMerge.WinMerge","WinMerge","Development","Open-source file and folder comparison tool.",foss=True),
    AppSpec("9WZDNCRFJ3TJ","Netflix","Entertainment","Netflix Windows app from Microsoft Store.",source="msstore"),
    AppSpec("TheDocumentFoundation.LibreOffice","LibreOffice","Productivity","Open-source office suite.",foss=True),
    AppSpec("Microsoft.Teams","Microsoft Teams","Productivity","Microsoft collaboration and meetings app."),
    AppSpec("ElementLabs.LMStudio","LM Studio","AI","Local LLM desktop app for running models on your PC."),
    AppSpec("Stremio.Stremio","Stremio","Media","Windows desktop media center."),
    AppSpec("AppWork.JDownloader","JDownloader 2","Utilities","Download manager with queueing and archive extraction."),
    AppSpec("9N9WCLWDQS5J","Bluetooth Audio Receiver","Music","Receive Bluetooth audio from paired devices on Windows.",source="msstore"),
]


@dataclass(frozen=True)
class UpdateReport:
    available: int
    updated: int = 0
    remaining: int = 0
    attempted: int = 0
    output: str = ""

    @property
    def failed(self) -> int:
        return max(0, self.attempted - self.updated)

    @property
    def clean(self) -> bool:
        return self.remaining == 0


def parse_upgrade_count(output: str) -> int:
    """Extract the number of available upgrades from WinGet text output."""
    text = output or ""
    patterns = (
        r"(?im)^\\s*(\\d+)\\s+upgrade(?:s)?\\s+available\\.?\\s*$",
        r"(?im)^\\s*(\\d+)\\s+package(?:s)?\\s+have\\s+upgrade(?:s)?\\s+available\\.?\\s*$",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))

    catalog_ids = {app.id.lower() for app in CATALOG}
    found = {
        package_id
        for package_id in catalog_ids
        if re.search(rf"(?i)(?<![A-Za-z0-9_.-]){re.escape(package_id)}(?![A-Za-z0-9_.-])", text)
    }
    return len(found)


def upgrade_report() -> UpdateReport:
    """Scan for upgrades and return a structured count for the UI."""
    output = upgrade_available()
    available = parse_upgrade_count(output)
    return UpdateReport(available=available, attempted=available, remaining=available, output=output)


def upgrade_all_report() -> UpdateReport:
    """Upgrade all available packages and verify the remaining count."""
    before = upgrade_report()
    if before.available == 0:
        return before

    output, code = _winget(
        [
            "upgrade", "--all", "--accept-package-agreements",
            "--accept-source-agreements", "--disable-interactivity",
        ],
        600,
    )
    if code and "No applicable upgrade found" not in output:
        raise RuntimeError(output or "WinGet upgrade failed.")

    after = upgrade_report()
    updated = max(0, before.available - after.available)
    return UpdateReport(
        available=before.available,
        updated=updated,
        remaining=after.available,
        attempted=before.available,
        output=output or "No applicable upgrades found.",
    )

def _winget(args: list[str], timeout: int = 180):
    result = run_executable("winget", args, timeout)
    return result.stdout or result.stderr or "", result.returncode

def ensure_winget() -> None:
    output, code = _winget(["--version"], 30)
    if code != 0 or not output.strip():
        raise RuntimeError("WinGet is unavailable. Install or repair Microsoft App Installer first.")

def installed_apps() -> str:
    ensure_winget()
    output, code = _winget(["list","--accept-source-agreements"],120)
    if code and not output:
        raise RuntimeError("WinGet inventory unavailable.")
    return output

def installed(package_id: str, source: str = "winget") -> bool:
    ensure_winget()
    args=["list","--id",package_id,"--exact","--accept-source-agreements"]
    if source: args += ["--source",source]
    output, code = _winget(args,60)
    lowered=output.lower()
    return code == 0 and bool(output.strip()) and not any(
        text in lowered for text in ("no installed package found","no installed package","no package found")
    )

def install(package_id: str) -> str:
    spec=next((app for app in CATALOG if app.id == package_id),None)
    if spec is None:
        raise ValueError("Package is not in the curated Windows 11 application catalog.")
    ensure_winget()
    args=["install","--id",spec.id,"--exact","--accept-package-agreements","--accept-source-agreements"]
    if spec.source: args += ["--source",spec.source]
    output,code=_winget(args,600)
    if code: raise RuntimeError(output or f"WinGet failed for {spec.name}.")
    return output or f"Installed {spec.name}."

def install_selected(package_ids: Iterable[str]) -> str:
    ids=list(dict.fromkeys(package_ids))
    if not ids: return "No applications selected."
    results=[]
    for package_id in ids:
        try: results.append(f"[OK] {package_id}\n{install(package_id)}")
        except Exception as exc: results.append(f"[FAILED] {package_id}\n{exc}")
    return "\n\n".join(results)

def upgrade_available() -> str:
    ensure_winget()
    output,code=_winget(
        ["upgrade","--accept-source-agreements","--disable-interactivity"],
        120,
    )
    if code and not output:
        raise RuntimeError("WinGet upgrade inventory unavailable.")
    return output


def upgrade_all() -> str:
    ensure_winget()
    output,code=_winget(
        [
            "upgrade",
            "--all",
            "--accept-package-agreements",
            "--accept-source-agreements",
            "--disable-interactivity",
        ],
        600,
    )
    if code and "No applicable upgrade found" not in output:
        raise RuntimeError(output or "WinGet upgrade failed.")
    return output or "No applicable upgrades found."
