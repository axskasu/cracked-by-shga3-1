from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box
import colorama
from colorama import Fore, Style

LOGO = '''\n⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢤⣶⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣤⡾⠿⢿⡀⠀⠀⠀⠀⣠⣶⣿⣷⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣦⣴⣿⡋⠀⠀⠈⢳⡄⠀⢠⣾⣿⠁⠈⣿⡆⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⣰⣿⣿⠿⠛⠉⠉⠁⠀⠀⠀⠹⡄⣿⣿⣿⠀⠀⢹⡇⠀⠀⠀
⠀⠀⠀⠀⠀⣠⣾⡿⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⣰⣏⢻⣿⣿⡆⠀⠸⣿⠀⠀⠀
⠀⠀⠀⢀⣴⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣾⣿⣿⣆⠹⣿⣷⠀⢘⣿⠀⠀⠀ /!\ shit cracked by reversinglabs /!\ 
⠀⠀⢀⡾⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⣿⣿⠋⠉⠛⠂⠹⠿⣲⣿⣿⣧⠀⠀ /!\ join discord.gg/erpl /!\ 
⠀⢠⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⣿⣿⣿⣷⣾⣿⡇⢀⠀⣼⣿⣿⣿⣧⠀ /!\ eurosearcher.xyz otp /!\ 
⠰⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⡘⢿⣿⣿⣿⠀ /!\ just get a brain and stop protecting /!\ 
⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⸸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⣷⡈⠿⢿⣿⡆ /!\ your shit with keyauth /!\ 
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠛⠁⢙⠛⣿⣿⣿⣿⡟⠀⡿⠀⠀⢀⣿⡇
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣶⣤⣉⣛⠻⠇⢠⣿⣾⣿⡄⢻⡇
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣦⣤⣾⣿⣿⣿⣿⣆⠁
   ███████╗██╗ ██████╗ █████╗      ██████╗██╗  ██╗███████╗ ██████╗██╗  ██╗███████╗██████╗
   ██╔════╝██║██╔════╝██╔══██╗    ██╔════╝██║  ██║██╔════╝██╔════╝██║ ██╔╝██╔════╝██╔══██╗
   ███████╗██║██║     ███████║    ██║     ███████║█████╗  ██║     █████╔╝ █████╗  ██████╔╝
   ╚════██║██║██║     ██╔══██║    ██║     ██╔══██║██╔══╝  ██║     ██╔═██╗ ██╔══╝  ██╔══██╗
   ███████║██║╚██████╗██║  ██║    ╚██████╗██║  ██║███████╗╚██████╗██║  ██╗███████╗██║  ██║
   ╚══════╝╚═╝ ╚═════╝╚═╝  ╚═╝     ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝

'''

class UI:
    def __init__(
        self,
        logger,
        keyauth_app=None,
        license_key=None,
        owner="SicarioStore",
        dev="OufRob9, LONYX and SICARIO",
        discord="Discord: .gg/sicariostore",
    ):
        self.logger = logger
        self.keyauth_app = keyauth_app
        self.license_key = license_key
        self.owner = owner
        self.dev = dev
        self.discord = discord
        self.total_accounts = 0

    def set_total(self, total: int):
        self.total_accounts = total

    def __rich__(self) -> Layout:
        return self.generate_layout()

    def generate_layout(self) -> Layout:
        layout = Layout()
        layout.split(
            Layout(name="header", size=22),
            Layout(name="info", size=4),
            Layout(name="stats", size=3),
            Layout(name="console"),
            Layout(name="footer", size=3),
        )

        _var_var_1 = self.logger._diagonal_gradient_text(LOGO.strip("\n"), (255, 30, 30), (100, 0, 0))
        _var_var_1.justify = "center"
        layout["header"].update(Panel(_var_var_1, border_style="rgb(200,20,20)", box=box.ROUNDED))

        _var_var_2 = Table.grid(expand=True)
        _var_var_2.add_column(justify="center", ratio=1)
        _var_var_3 = Text()
        _var_var_3.append("Owner: ", style="bold white")
        _var_var_3.append(f"{self.owner}", style="red")
        _var_var_3.append("  |  ", style="bold white")
        _var_var_3.append("Devs: ", style="bold white")
        _var_var_3.append(f"{self.dev}", style="red")

        _var_var_4 = Text()
        if self.license_key and len(self.license_key) > 8:
            _var_var_5 = self.license_key[:4] + "****" + self.license_key[-4:]
        else:
            _var_var_5 = self.license_key if self.license_key else "N/A"
        _var_var_4.append("License Key: ", style="bold white")
        _var_var_4.append(f"{_var_var_5}", style="cyan")
        _var_var_2.add_row(_var_var_3)
        _var_var_2.add_row(_var_var_4)

        _var_var_6 = self.logger._static_gradient_text(" Dashboard ")
        layout["info"].update(Panel(_var_var_2, title=_var_var_6, border_style="rgb(200,20,20)", box=box.ROUNDED))

        _var_var_7 = self.logger.stats
        _var_var_8 = _var_var_7.get("bad", 0)
        _var_var_9 = _var_var_7.get("hit", 0)
        _var_var_10 = _var_var_7.get("ogs", 0)
        _var_var_11 = _var_var_7.get("2fa", 0)
        _var_var_12 = _var_var_7.get("remain", 0)

        _var_var_13 = Text()
        _var_var_13.append(f" BAD: {_var_var_8} ", style="bold white on red")
        _var_var_13.append("   ")
        _var_var_13.append(f" HIT: {_var_var_9} ", style="bold white on green")
        _var_var_13.append("   ")
        _var_var_13.append(f" OGS: {_var_var_10} ", style="bold white on yellow")
        _var_var_13.append("   ")
        _var_var_13.append(f" 2FA: {_var_var_11} ", style="bold white on magenta")
        _var_var_13.append("   ")
        _var_var_13.append(f" REMAIN: {_var_var_12} ", style="bold white on blue")
        _var_var_13.justify = "center"

        _var_var_14 = self.logger._static_gradient_text(" Statistics ")
        layout["stats"].update(Panel(_var_var_13, title=_var_var_14, border_style="rgb(200,20,20)", box=box.ROUNDED))

        _var_var_15 = self.logger.all_logs[-15:]
        _var_var_16 = Text("\n").join(_var_var_15)
        _var_var_17 = self.logger._static_gradient_text(" Live Console Logs ")
        layout["console"].update(
            Panel(
                _var_var_16,
                title=_var_var_17,
                border_style="rgb(200,20,20)",
                padding=(1, 2),
                box=box.ROUNDED,
            )
        )

        _var_var_18 = self.logger._static_gradient_text(self.discord)
        _var_var_18.stylize("bold")
        _var_var_18.justify = "center"
        layout["footer"].update(Panel(_var_var_18, border_style="rgb(200,20,20)", box=box.ROUNDED))

        return layout