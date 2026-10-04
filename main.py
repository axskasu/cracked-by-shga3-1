import asyncio
import os
import sys

if sys.platform == "win32":
    os.system("chcp 65001 > nul 2>&1")

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from rich import box
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.table import Table

from src.auth import authenticate_user
from src.config import config
from src.logger import logger
from src.ui import LOGO, UI
from src.utils import load_combos
from src.webhook import webhook_manager
from src.worker import worker


async def configure_webhooks_menu(console: Console) -> None:

    def format_status(url: str) -> tuple[str, str]:
        if not url:
            return ("[bold red]Désactivé[/bold red]", "—")
        url = str(url).strip()
        if len(url) > 30:
            url = url[:22] + "..." + url[-8:]
        return ("[bold green]Actif[/bold green]", url)

    while True:
        os.system("cls" if os.name == "nt" else "clear")

        gradient = logger._diagonal_gradient_text(LOGO.strip("\n"), (255, 30, 30), (100, 0, 0))
        gradient.justify = "center"
        console.print(gradient)

        table = Table(
            title="[bold white]Configuration des Webhooks Discord[/bold white]",
            border_style="rgb(200,20,20)",
            box=box.ROUNDED,
            expand=True,
        )
        table.add_column("Type de Webhook", style="bold white", ratio=2)
        table.add_column("Statut", justify="center", ratio=1)
        table.add_column("URL (Aperçu)", style="dim", ratio=3)

        status = format_status
        live_label, live_url_preview = status(webhook_manager.live_url)
        hit_label, hit_url_preview = status(webhook_manager.hit_url)
        twofa_label, twofa_url_preview = status(webhook_manager.twofa_url)
        shortcode_label, shortcode_url_preview = status(webhook_manager.shortcode_url)
        screenshot_label, screenshot_url_preview = status(webhook_manager.screenshot_url)

        table.add_row("1. Live Status (Embed en direct)", live_label, live_url_preview)
        table.add_row("2. Hit / Valide (Embed complet + Screens)", hit_label, hit_url_preview)
        table.add_row("3. 2FA Requis (Notification)", twofa_label, twofa_url_preview)
        table.add_row("4. Shortcodes (Format brut)", shortcode_label, shortcode_url_preview)
        table.add_row("5. Screenshot Seul (Capture directe)", screenshot_label, screenshot_url_preview)
        console.print(table)

        options_text = (
            "[bold white]1-5.[/bold white] [bold cyan]Modifier l'URL d'un webhook[/bold cyan]\n"
            "[bold white]6.[/bold white]   [bold yellow]Tester tous les webhooks configurés[/bold yellow]\n"
            "[bold white]7.[/bold white]   [bold red]Effacer toutes les URLs[/bold red]\n"
            "[bold white]0.[/bold white]   [bold green]Retour au Menu Principal[/bold green]"
        )
        console.print(
            Panel(
                options_text,
                title="[bold white]Options Webhooks[/bold white]",
                border_style="rgb(200,20,20)",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )

        try:
            choice = Prompt.ask("Votre choix", choices=["0", "1", "2", "3", "4", "5", "6", "7"])
        except (KeyboardInterrupt, EOFError):
            return

        if choice == "0":
            return

        if choice in ("1", "2", "3", "4", "5"):
            webhook_map = {
                "1": ("webhooks.live_url", "Live Webhook (Embed direct)"),
                "2": ("webhooks.hit_url", "Hit / Valide Webhook"),
                "3": ("webhooks.twofa_url", "2FA Webhook"),
                "4": ("webhooks.shortcode_url", "Shortcodes Webhook"),
                "5": ("webhooks.screenshot_url", "Screenshot Webhook"),
            }
            config_key, label = webhook_map[choice]
            current = config.get(config_key, "") or ""
            console.print(f"\n[bold yellow]Configuration : {label}[/bold yellow]")
            console.print("[dim]Collez l'URL de votre webhook Discord (ou appuyez sur Entrée pour vider) :[/dim]")
            new_url = Prompt.ask("URL", default=current).strip()

            config.set(config_key, new_url)
            config.save()
            console.print("[bold green]Webhook mis à jour avec succès ![/bold green]")
            await asyncio.sleep(1)

        elif choice == "6":
            console.print("\n[bold yellow]Lancement des tests de connexion...[/bold yellow]")
            webhooks_to_test = [
                ("Live Webhook", webhook_manager.live_url),
                ("Hit Webhook", webhook_manager.hit_url),
                ("2FA Webhook", webhook_manager.twofa_url),
                ("Shortcode Webhook", webhook_manager.shortcode_url),
                ("Screenshot Webhook", webhook_manager.screenshot_url),
            ]
            any_configured = False
            for label, url in webhooks_to_test:
                if not url:
                    continue
                any_configured = True
                success, message = webhook_manager.test_webhook(url)
                if success:
                    console.print(f"[bold green]{label} :[/bold green] Connexion réussie !")
                else:
                    console.print(f"[bold red]{label} :[/bold red] {message}")

            if not any_configured:
                console.print("[bold yellow]Aucun webhook configuré à tester.[/bold yellow]")
            Prompt.ask("\nAppuyez sur Entrée pour continuer")

        elif choice == "7":
            for key in (
                "webhooks.live_url",
                "webhooks.hit_url",
                "webhooks.twofa_url",
                "webhooks.shortcode_url",
                "webhooks.screenshot_url",
            ):
                config.set(key, "")
            config.save()
            console.print("[bold red]Tous les webhooks ont été réinitialisés.[/bold red]")
            await asyncio.sleep(1)


async def show_menu() -> None:
    console = Console(legacy_windows=False)

    while True:
        sys.stdout.reconfigure(encoding="utf-8")
        os.system("chcp 65001")
        os.system("title CRACKED BY /ERPL")
        os.system("cls" if os.name == "nt" else "clear")

        gradient = logger._diagonal_gradient_text(LOGO.strip("\n"), (255, 30, 30), (100, 0, 0))
        gradient.justify = "center"
        console.print(gradient)

        menu_text = (
            "\n   [bold white]\\[1][/bold white] [bold red]Start Checker[/bold red]"
            "        - [dim]Begin checking accounts[/dim]\n"
            "\n   [bold white]\\[2][/bold white] [bold red]Configuration[/bold red]"
            "        - [dim]Modify settings and threads[/dim]\n"
            "\n   [bold white]\\[3][/bold white] [bold red]Discord Webhooks[/bold red]"
            "     - [dim]Configure live, hits & 2FA webhooks[/dim]\n"
            "\n   [bold white]\\[4][/bold white] [bold red]Exit[/bold red]"
            "                 - [dim]Close the application[/dim]\n"
        )
        console.print(
            Panel(
                menu_text,
                title="[bold white]Main Dashboard[/bold white]",
                border_style="red",
                box=box.DOUBLE_EDGE,
                padding=(1, 4),
            )
        )

        try:
            choice = Prompt.ask(
                "\n[bold red]>[/bold red] [bold white]Select Option[/bold white]",
                choices=["1", "2", "3", "4"],
            )
        except (KeyboardInterrupt, EOFError):
            print("\nStop requested.")
            exit(0)

        if choice == "1":
            return None

        elif choice == "2":
            try:
                threads = IntPrompt.ask(
                    "[bold red]>[/bold red] [bold white]Threads[/bold white] [dim](Recommended: 3)[/dim]",
                    default=config.get("threads", 3),
                )
                combo_path = (
                    Prompt.ask(
                        "[bold red]>[/bold red] [bold white]Combo file/folder path[/bold white]",
                        default=config.get("paths.combo_file", "input/combo.txt"),
                    )
                    .strip()
                    .strip('"')
                    .strip("'")
                )
                output_folder = (
                    Prompt.ask(
                        "[bold red]>[/bold red] [bold white]Output folder path[/bold white]",
                        default=config.get("paths.output_folder", "output/"),
                    )
                    .strip()
                    .strip('"')
                    .strip("'")
                )
            except (KeyboardInterrupt, EOFError):
                print("\nStop requested.")
                exit(0)

            config.set("threads", threads)
            config.set("paths.combo_file", combo_path)
            config.set("paths.output_folder", output_folder)
            config.save()
            console.print("\n[bold green]Configuration saved![/bold green]")
            await asyncio.sleep(1)

        elif choice == "3":
            await configure_webhooks_menu(console)

        elif choice == "4":
            exit(0)


async def main() -> None:
    if getattr(sys, "frozen", False) or "__compiled__" in globals():
        app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))

    os.chdir(app_dir)
    os.system("cls" if os.name == "nt" else "clear")

    authenticated, keyauth_app, license_key = authenticate_user()
    if not authenticated:
        input("\nPress Enter to exit...")
        return None

    os.makedirs("output", exist_ok=True)
    os.makedirs("input", exist_ok=True)

    if not os.path.exists("input/combo.txt"):
        with open("input/combo.txt", "w", encoding="utf-8"):
            pass

    if not os.path.exists("input/rare_skin.txt"):
        with open("input/rare_skin.txt", "w", encoding="utf-8"):
            pass

    while True:
        await show_menu()

        combos = load_combos()
        if not combos:
            logger.error("Aucun combo chargé. Veuillez placer vos comptes dans input/combo.txt")
            console = Console(legacy_windows=False)
            console.print("\n[bold red]Aucun combo trouvé ![/bold red]")
            console.print("[dim]Placez vos combos au format email:motdepasse dans [bold white]input/combo.txt[/bold white][/dim]\n")
            try:
                Prompt.ask("Appuyez sur Entrée pour revenir au menu principal")
            except Exception:
                pass
        else:
            break

    total = len(combos)
    logger.stats["remain"] = total
    logger.info(f"Starting check for {total} accounts...")

    webhook_manager.start_live(total=total)
    params = {"output_folder": config.get("paths.output_folder", "output/")}

    ui = UI(logger, keyauth_app, license_key)
    ui.set_total(total)

    queue = asyncio.Queue()
    for combo in combos:
        queue.put_nowait(combo)

    threads = config.get("threads", 3)
    semaphore = asyncio.Semaphore(threads)
    os.system("cls" if os.name == "nt" else "clear")

    with Live(ui, refresh_per_second=4):
        tasks = []
        for _ in range(threads):
            tasks.append(asyncio.create_task(worker(queue, params, semaphore)))

        try:
            await asyncio.gather(*tasks)
        except (asyncio.CancelledError, KeyboardInterrupt):
            pass

    webhook_manager.finish_live()
    logger.success("Checking finished.")
    print("\n\nChecking finished. Check your 'output' folder. Press Enter to exit.")
    try:
        input()
    except Exception:
        pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Script termination requested by user.")