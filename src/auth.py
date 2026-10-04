import os
import sys
import json as jsond
import time
import platform
import subprocess
from datetime import datetime, timezone, timedelta
from rich.console import Console
from rich.panel import Panel
from rich import box
from rich.align import Align
from src.logger import logger
from src.ui import LOGO

try:
    import certifi

    os.environ["SSL_CERT_FILE"] = certifi.where()
    os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
except Exception:
    pass

if os.name == "nt":
    import win32security

try:
    import requests
    from discord_interactions import verify_key
except Exception:
    pass

AUTH_BYPASS = True  # dev: skip KeyAuth license validation to reach the menu


class others:
    @staticmethod
    def get_hwid():
        if platform.system() == "Linux":
            with open("/etc/machine-id") as f:
                return f.read().strip()
        elif platform.system() == "Windows":
            try:
                user_id = os.getlogin()
                sid = win32security.LookupAccountName(None, user_id)[0]
                return win32security.ConvertSidToStringSid(sid)
            except Exception:
                p = subprocess.Popen(
                    "wmic useraccount where name='%username%' get sid",
                    stdout=subprocess.PIPE,
                    shell=True,
                )
                out, _ = p.communicate()
                return out.split(b"\n")[1].strip().decode()
        elif platform.system() == "Darwin":
            p = subprocess.Popen(
                "ioreg -l | grep IOPlatformSerialNumber",
                stdout=subprocess.PIPE,
                shell=True,
            )
            output = p.communicate()[0]
            return output.decode().split("=", 1)[1].replace(" ", "")[1:-2]
        return "UNKNOWN_HWID"


class KeyAuth:
    def __init__(self, name, ownerid, version, hash_to_check, secret=""):
        if len(ownerid) != 10:
            raise Exception("Invalid OwnerID")
        self.name = name
        self.ownerid = ownerid
        self.version = version
        self.hash_to_check = hash_to_check
        self.secret = secret
        self.sessionid = ""
        self.initialized = False

    def init(self):
        if self.sessionid != "":
            return (False, "Already initialized")
        response = self._KeyAuth__do_request(
            {
                "type": "init",
                "ver": self.version,
                "hash": self.hash_to_check,
                "name": self.name,
                "ownerid": self.ownerid,
            }
        )
        if not response:
            return (False, "Failed to connect to KeyAuth")
        if response == "KeyAuth_Invalid":
            return (False, "Application doesn't exist")
        try:
            response_data = jsond.loads(response)
            if not response_data.get("success", False):
                return (False, response_data.get("message", "Error"))
            self.sessionid = response_data.get("sessionid", "")
            self.initialized = True
            return (True, "Initialized")
        except Exception:
            return (False, "Invalid response")

    def license(self, key, hwid=None):
        if not self.initialized:
            return (False, "Initialize first")
        if hwid is None:
            hwid = others.get_hwid()
        response = self._KeyAuth__do_request(
            {
                "type": "license",
                "key": key,
                "hwid": hwid,
                "sessionid": self.sessionid,
                "name": self.name,
                "ownerid": self.ownerid,
            }
        )
        if not response:
            return (False, "Failed to connect to KeyAuth")
        try:
            response_data = jsond.loads(response)
            return (response_data.get("success", False), response_data.get("message", ""))
        except Exception:
            return (False, "Invalid response")

    def __do_request(self, post_data):
        url = "https://keyauth.win/api/1.3/"
        session = requests.Session()
        try:
            session.verify = certifi.where()
        except Exception:
            pass
        for _ in range(3):
            try:
                res = session.post(url, data=post_data, timeout=15)
                if res.status_code != 200:
                    time.sleep(0.5)
                    continue
                response = res.text
                if not response:
                    continue
                signature = res.headers.get("x-signature-ed25519")
                timestamp = res.headers.get("x-signature-timestamp")
                if signature and timestamp:
                    try:
                        signature_time = datetime.fromtimestamp(int(timestamp), timezone.utc)
                        if abs(datetime.now(timezone.utc) - signature_time).total_seconds() <= 600:
                            if verify_key(
                                response.encode("utf-8"),
                                signature,
                                timestamp,
                                "5586b4bc69c7a4b487e4563a4cd96afd39140f919bd31cea7d1c6a1e8439422b",
                            ):
                                return response
                    except Exception:
                        pass
                try:
                    response_data = jsond.loads(response)
                    if "success" in response_data:
                        return response
                except Exception:
                    pass
                return response
            except Exception:
                time.sleep(0.5)
                continue
        return None


def authenticate_user() -> tuple[bool, object, str]:
    console = Console(legacy_windows=False)
    console.clear()
    appdata = os.getenv("APPDATA", "")
    config_dir = os.path.join(appdata, "sicariocheck")
    os.makedirs(config_dir, exist_ok=True)
    license_file = os.path.join(config_dir, "license.txt")

    logo = logger._diagonal_gradient_text(LOGO.strip("\n"), (255, 30, 30), (100, 0, 0))
    logo.justify = "center"

    keyauth = KeyAuth(
        name="sicariocheck",
        ownerid="2etBnT3o7F",
        version="1.0",
        hash_to_check="",
    )
    if AUTH_BYPASS:
        console.print(logo)
        return (True, keyauth, "")
    success, message = keyauth.init()
    if not success:
        console.print(
            Align.center(
                Panel(f"[bold red]Initialization Failed:[/bold red] {message}", border_style="red")
            )
        )
        return (False, None, "")

    console.print(logo)
    saved_key = None
    if os.path.exists(license_file):
        try:
            with open(license_file, "r", encoding="utf-8") as f:
                saved_key = f.read().strip()
        except Exception:
            pass
    if saved_key:
        with console.status("[bold green]Auto-login... Validation de la clé...[/bold green]", spinner="dots2"):
            success, message = keyauth.license(saved_key)
            time.sleep(1)
        if success:
            console.print(
                Align.center(
                    Panel(
                        f"[bold green]Bon retour ![/bold green]\n{message}",
                        border_style="green",
                        box=box.ROUNDED,
                        padding=(1, 2),
                    )
                )
            )
            time.sleep(1.5)
            return (True, keyauth, saved_key)
        else:
            console.print(
                Align.center(
                    Panel(
                        f"[bold yellow]Clé enregistrée invalide ou expirée.[/bold yellow] ({message})",
                        border_style="yellow",
                    )
                )
            )

    auth_panel = Panel(
        Align.center(
            "[bold white]Bienvenue sur EpicChecker[/bold white]\n[dim]Veuillez entrer votre clé de licence premium pour déverrouiller le logiciel.[/dim]"
        ),
        title="[bold red]Authentification Requise[/bold red]",
        border_style="red",
        box=box.DOUBLE_EDGE,
        padding=(1, 4),
    )
    console.print(Align.center(auth_panel))
    console.print("\n                    [bold red]>[/bold red] [bold white]Clé de Licence:[/bold white] ", end="")
    try:
        license_key = input().strip()
    except (KeyboardInterrupt, EOFError):
        return (False, None, "")

    with console.status("[bold red]Validation de la clé auprès de KeyAuth...[/bold red]", spinner="bouncingBar"):
        success, message = keyauth.license(license_key)
        time.sleep(1)

    if success:
        try:
            with open(license_file, "w", encoding="utf-8") as f:
                f.write(license_key)
        except Exception:
            pass
        console.print(
            Align.center(
                Panel(
                    f"[bold green]Authentification Réussie ![/bold green]\n{message}",
                    border_style="green",
                    box=box.ROUNDED,
                    padding=(1, 2),
                )
            )
        )
        time.sleep(1.5)
        return (True, keyauth, license_key)
    else:
        console.print(
            Align.center(
                Panel(
                    f"[bold red]Échec de l'authentification :[/bold red]\n{message}",
                    border_style="red",
                    box=box.HEAVY,
                )
            )
        )
        return (False, None, "")