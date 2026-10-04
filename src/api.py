import asyncio
import base64
import json
import re
import requests
from urllib.parse import parse_qs, urlparse


RARE_SKINS_LOWER = {
    "cid_017_athena_commando_m": "Aerial Assault Trooper",
    "cid_028_athena_commando_f": "Renegade Raider",
    "cid_035_athena_commando_m_medieval": "Black Knight",
    "cid_030_athena_commando_m_halloween": "Skull Trooper",
    "cid_029_athena_commando_f_halloween": "Ghoul Trooper",
    "cid_022_athena_commando_f": "Recon Expert",
    "cid_019_athena_commando_m": "Infiltrator",
    "cid_020_athena_commando_m": "Special Forces",
    "cid_021_athena_commando_f": "Brawler",
    "cid_023_athena_commando_f": "Munitions Expert",
    "cid_024_athena_commando_f": "Recon Specialist",
    "cid_025_athena_commando_m": "First Strike Specialist",
    "cid_026_athena_commando_m": "Desperado",
    "cid_027_athena_commando_f": "Survival Specialist",
    "cid_032_athena_commando_m_medieval": "Blue Squire",
    "cid_033_athena_commando_f_medieval": "Royale Knight",
    "cid_034_athena_commando_f_medieval": "Red Knight",
    "cid_031_athena_commando_m_retro": "Raptor",
    "cid_036_athena_commando_m_wintercamo": "Absolute Zero",
    "cid_037_athena_commando_f_wintercamo": "Arctic Assassin",
    "cid_038_athena_commando_m_disco": "Funk Ops",
    "cid_039_athena_commando_f_disco": "Sparkle Specialist",
    "cid_040_athena_commando_m_district": "Devastator",
    "cid_041_athena_commando_f_district": "Dominator",
    "cid_042_athena_commando_m_cyberpunk": "Circuit Breaker",
    "cid_043_athena_commando_f_stealth": "Shadow Ops",
    "cid_044_athena_commando_f_scipop": "Brite Bomber",
    "cid_045_athena_commando_m_holidaysweater": "Yuletide Ranger",
    "cid_046_athena_commando_f_holidaysweater": "Nog Ops",
    "cid_047_athena_commando_f_holidayreindeer": "Red-Nosed Raider",
    "cid_048_athena_commando_f_holidaygingerbread": "Ginger Gunner",
    "cid_084_athena_commando_m_assassin": "The Reaper",
    "cid_082_athena_commando_m_scavenger": "Rust Lord",
    "cid_083_athena_commando_f_scavenger": "Renegade",
    "cid_085_athena_commando_m_twitch": "Twitch Prime",
    "cid_096_athena_commando_f_fable": "Fable",
    "cid_097_athena_commando_f_rockerpunk": "Power Chord",
    "cid_098_athena_commando_f_rockerpunk": "Power Chord (alt)",
    "cid_113_athena_commando_m_bluemystery": "Carbide",
    "cid_114_athena_commando_f_tacticalwoodland": "Trailblazer",
    "cid_116_athena_commando_m_carbideblack": "Omega",
    "cid_117_athena_commando_m_raven": "Raven",
    "cid_118_athena_commando_f_valor": "Valor",
    "cid_120_athena_commando_m_samuraiblue": "Musha",
    "cid_121_athena_commando_f_samuraiblue": "Hime",
    "cid_124_athena_commando_f_auroraglow": "Glow",
    "cid_125_athena_commando_m_tacticalwoodland": "Sledgehammer",
    "cid_127_athena_commando_m_mating": "Magnus",
    "cid_128_athena_commando_f_mating": "Huntress",
    "cid_130_athena_commando_m_m_med": "Dark Voyager",
    "cid_131_athena_commando_f_m_med": "Dark Vanguard",
    "cid_132_athena_commando_f_bandageninja": "Fate",
    "cid_133_athena_commando_f_bandageninja": "Fate (alt)",
    "cid_134_athena_commando_m_raptorblackops": "Havoc",
    "cid_135_athena_commando_f_raptorblackops": "Criterion",
    "cid_137_athena_commando_f_warpaint": "Native",
    "cid_138_athena_commando_m_warpaint": "War Paint",
    "cid_139_athena_commando_m_bobcat": "Battle Hound",
    "cid_140_athena_commando_m_snake": "Zoey",
    "cid_141_athena_commando_f_snake": "Zoey",
    "cid_142_athena_commando_m_strawberrypilot": "Stealth Reflex",
    "cid_143_athena_commando_f_strawberrypilot": "Reflex",
    "cid_144_athena_commando_m_soccer": "Aerial Threat",
    "cid_145_athena_commando_f_soccer": "Finesse Finisher",
    "cid_146_athena_commando_m_soccer": "Stalwart Sweeper",
    "cid_147_athena_commando_f_soccer": "Clinical Crosser",
    "cid_148_athena_commando_m_soccer": "Midfield Maestro",
    "cid_149_athena_commando_f_soccer": "Dynamic Dribbler",
    "cid_150_athena_commando_m_soccer": "Super Striker",
    "cid_151_athena_commando_f_soccer": "Super Striker",
    "cid_160_athena_commando_m_toxik": "Toxic Trooper",
    "cid_161_athena_commando_f_toxik": "Toxic Trooper",
    "cid_162_athena_commando_m_neoncat": "Lynx",
    "cid_163_athena_commando_f_neoncat": "Lynx",
    "cid_164_athena_commando_m_viking": "Magnus",
    "cid_165_athena_commando_f_viking": "Huntress",
    "cid_166_athena_commando_m_wreck": "Wreck Raider",
    "cid_167_athena_commando_f_wreck": "Scrapyard",
    "cid_168_athena_commando_m_shogun": "Shogun",
    "cid_169_athena_commando_f_shogun": "Hime",
    "cid_170_athena_commando_m_luchador": "Lucha",
    "cid_171_athena_commando_f_luchador": "Lucha",
    "cid_172_athena_commando_m_samuraiultra": "Musha",
    "cid_173_athena_commando_f_samuraiultra": "Hime",
    "cid_174_athena_commando_m_tacticalwoodland": "Sledgehammer",
    "cid_175_athena_commando_f_tacticalwoodland": "Trailblazer",
    "cid_176_athena_commando_m_assaulttrooper": "Highrise Assault Trooper",
    "cid_177_athena_commando_f_assaulttrooper": "Tower Recon Specialist",
    "cid_178_athena_commando_m_starwalker": "Galaxy",
    "cid_179_athena_commando_f_starwalker": "Galaxy Scout",
    "cid_180_athena_commando_m_tacticalurban": "Sub Commander",
    "cid_181_athena_commando_f_tacticalurban": "Tactics Officer",
    "cid_182_athena_commando_m_modernmilitary": "Squad Leader",
    "cid_183_athena_commando_f_modernmilitary": "Squad Leader",
    "cid_184_athena_commando_m_modernmilitaryred": "Sgt. Green",
    "cid_185_athena_commando_f_modernmilitaryred": "Sgt. Green",
    "cid_186_athena_commando_m_gummi": "Gumshoe",
    "cid_187_athena_commando_f_gummi": "Sleuth",
    "cid_188_athena_commando_f_streetracerwhite": "Whiteout",
    "cid_189_athena_commando_m_streetracerwhite": "Whiteout",
    "cid_190_athena_commando_m_streetracermetallic": "Stealth",
    "cid_191_athena_commando_f_streetracermetallic": "Stealth",
    "cid_192_athena_commando_m_streetracerdisrupt": "Vertex",
    "cid_193_athena_commando_f_streetracerdisrupt": "Vertex",
    "cid_194_athena_commando_m_ravenquill": "Raven",
    "cid_195_athena_commando_f_ravenquill": "Raven",
    "cid_196_athena_commando_m_shark": "Chomp Sr.",
    "cid_197_athena_commando_f_shark": "Cozy Chomps",
    "cid_198_athena_commando_m_bluedevil": "Blue Team Leader",
    "cid_199_athena_commando_f_bluedevil": "Blue Team Leader",
    "cid_200_athena_commando_m_darkninja": "Cloaked Shadow",
    "cid_201_athena_commando_f_darkninja": "Cloaked Shadow",
    "cid_174_athena_commando_f_carbidewhite": "Eon",
    "cid_175_athena_commando_m_carbidewhite": "Eon",
    "cid_313_athena_commando_m_kpopfashion": "Ikonic",
    "cid_342_athena_commando_m_streetracermetallic": "Stealth",
    "cid_343_athena_commando_f_streetracermetallic": "Stealth",
    "cid_386_athena_commando_m_streetopsneon": "Wonder",
    "cid_387_athena_commando_f_streetopsneon": "Wonder",
    "cid_397_athena_commando_f_treasurehunterfashion": "Aura",
    "cid_434_athena_commando_f_stealthhonor": "Honor Guard",
    "cid_441_athena_commando_f_cyberscifipink": "Dream",
    "cid_479_athena_commando_f_davinci": "Davinci",
    "cid_480_athena_commando_m_davinci": "Davinci",
    "cid_259_athena_commando_m_rockerpunk": "Stage 5",
    "cid_260_athena_commando_f_rockerpunk": "Stage 5",
    "cid_315_athena_commando_m_teriyakifish": "Fishstick",
    "cid_316_athena_commando_f_teriyakifish": "Fishstick",
    "cid_347_athena_commando_m_evilcowboy": "Deadfire",
    "cid_348_athena_commando_f_evilcowboy": "Calamity",
    "cid_370_athena_commando_m_evilbunny": "Bunny Wolf",
    "cid_371_athena_commando_f_evilbunny": "Bunny Wolf",
    "cid_372_athena_commando_m_evilbunny": "Bunny Wolf",
    "cid_373_athena_commando_f_evilbunny": "Bunny Wolf",
    "cid_a_001_athena_commando_f_streetfashionblack": "Shadow Ops (alt)",
    "cid_110_athena_commando_f_circuitbreaker": "Cipher",
    "cid_111_athena_commando_m_circuitbreaker": "Cipher",
    "cid_112_athena_commando_f_circuitbreaker": "Cipher",
    "Circuit Breaker": "Cipher",
}


class EpicGamesAPI:
    CLIENT_ID = "ec684b8c687f479fadea3cb2ad83f5c6"
    CLIENT_SECRET = "e1f31c211f28413186262d37a13fc84d"
    REDIRECT_URL = "https://www.epicgames.com/id/api/redirect?clientId=ec684b8c687f479fadea3cb2ad83f5c6&responseType=code"

    def __init__(self, page, context):
        self.page = page
        self.context = context
        self.access_token = None
        self.account_id = None
        self.headers = None

    async def get_auth_code(self):
        try:
            try:
                if hasattr(self.page, "get"):
                    await self.page.get(self.REDIRECT_URL)
                elif hasattr(self.page, "goto"):
                    await self.page.goto(self.REDIRECT_URL)
            except Exception:
                pass

            await asyncio.sleep(1.5)
            page_url = self.page.url
            auth_code = None

            if "authorizationCode=" in page_url or "code=" in page_url:
                query = parse_qs(urlparse(page_url).query)
                auth_code = (query.get("authorizationCode") or query.get("code") or [None])[0]

            if not auth_code:
                try:
                    if hasattr(self.page, "get_content"):
                        content = await self.page.get_content()
                    elif hasattr(self.page, "inner_text"):
                        content = await self.page.inner_text("body")
                    else:
                        content = ""

                    try:
                        data = json.loads(content)
                        auth_code = data.get("authorizationCode") or data.get("code")
                    except Exception:
                        pass

                    if not auth_code:
                        match = re.search(
                            r"(?:authorizationCode|code)[\"\s:=]+([a-zA-Z0-9]{20,})",
                            content,
                            re.I,
                        )
                        if match:
                            auth_code = match.group(1)
                except Exception:
                    return auth_code
        except Exception:
            return None
        return auth_code

    def authenticate(self, code):
        basic = base64.b64encode(
            f"{self.CLIENT_ID}:{self.CLIENT_SECRET}".encode()
        ).decode()
        try:
            response = requests.post(
                "https://account-public-service-prod.ol.epicgames.com/account/api/oauth/token",
                headers={
                    "Authorization": f"Basic {basic}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={"grant_type": "authorization_code", "code": code},
                timeout=15,
            )
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.account_id = data.get("account_id")
                if self.access_token and self.account_id:
                    self.headers = {
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json",
                    }
                    return True
        except Exception:
            pass
        return False

    def fetch_athena_profile(self):
        if not self.headers:
            return None
        try:
            response = requests.post(
                "https://fortnite-public-service-prod11.ol.epicgames.com/fortnite/api/game/v2/profile/"
                f"{self.account_id}/client/QueryProfile?profileId=athena",
                headers=self.headers,
                json={},
                timeout=15,
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None

    def fetch_common_core_profile(self):
        if not self.headers:
            return None
        try:
            response = requests.post(
                "https://fortnite-public-service-prod11.ol.epicgames.com/fortnite/api/game/v2/profile/"
                f"{self.account_id}/client/QueryProfile?profileId=common_core",
                headers=self.headers,
                json={},
                timeout=15,
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None

    def fetch_platforms(self):
        if not self.headers:
            return ["Auth Error"]
        platforms = []
        try:
            response = requests.get(
                "https://account-public-service-prod.ol.epicgames.com/account/api/public/account/"
                f"{self.account_id}/externalAuths",
                headers=self.headers,
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    for entry in data:
                        if isinstance(entry, dict) and "type" in entry:
                            platforms.append(entry["type"].upper())
            elif response.status_code == 404:
                pass
            else:
                platforms.append(f"HTTP {response.status_code}")
        except Exception as e:
            platforms.append(f"API Error ({e})")
        return platforms

    def fetch_ban_status(self):
        if not self.headers:
            return (False, "")
        try:
            response = requests.get(
                "https://account-public-service-prod.ol.epicgames.com/account/api/public/account/"
                f"{self.account_id}/ban",
                headers=self.headers,
                timeout=8,
            )
            if response.status_code == 200:
                data = response.json()
                is_banned = data.get("isBanned", False)
                reason = data.get("banReason", "") or data.get("reason", "")
                return (is_banned, reason)
        except Exception:
            pass
        return (False, "")

    def parse_athena_data(self, profile):
        profile_data = {}
        if "profileChanges" in profile and len(profile["profileChanges"]) > 0:
            profile_data = profile["profileChanges"][0].get("profile", {})
        if not profile_data and "profile" in profile:
            profile_data = profile["profile"]

        items = profile_data.get("items") or profile.get("items") or {}
        attributes = (profile_data.get("stats") or {}).get("attributes", {})

        skin_count = 0
        rare_skins = []
        rare_seen = set()

        for item in items.values():
            template_id = item.get("templateId", "")
            if template_id.lower().startswith("athenacharacter:"):
                costume_id = template_id.split(":", 1)[1]
                if costume_id.lower() in ("cid_random", "cid_default", "random"):
                    continue
                skin_count += 1
                costume_lower = costume_id.lower()
                if costume_lower in RARE_SKINS_LOWER:
                    skin_name = RARE_SKINS_LOWER[costume_lower]
                    if skin_name not in rare_seen:
                        rare_skins.append(skin_name)
                        rare_seen.add(skin_name)

        last_match = None
        match_date = (
            attributes.get("last_match_end_datetime")
            or attributes.get("last_match_end_date")
        )
        if not match_date:
            match_date = profile_data.get("updated") or profile.get("updated")
        if match_date:
            try:
                if "T" in str(match_date):
                    last_match = str(match_date).split("T")[0]
                else:
                    last_match = str(match_date)[:10]
            except Exception:
                last_match = str(match_date)[:19]

        return (skin_count, rare_skins, last_match)

    def parse_common_core_data(self, profile):
        v_bucks = 0
        try:
            profile_data = {}
            if "profileChanges" in profile and len(profile["profileChanges"]) > 0:
                profile_data = profile["profileChanges"][0].get("profile", {})
            if not profile_data and "profile" in profile:
                profile_data = profile["profile"]

            items = profile_data.get("items") or profile.get("items") or {}

            for item in items.values():
                template_id = item.get("templateId", "")
                if "Mtx" in template_id or template_id == "Currency:MtxPurchased":
                    quantity = item.get("quantity", 0)
                    if isinstance(quantity, (int, float)) and quantity > v_bucks:
                        v_bucks = int(quantity)
        except Exception:
            pass
        return v_bucks

    async def get_all_account_info(self):
        code = await self.get_auth_code()
        if not code:
            return (0, [], None, None, False, [], False, "", "")

        if not await self.authenticate(code):
            return (0, [], None, None, False, [], False, "", "")

        athena_profile = self.fetch_athena_profile()
        if not athena_profile:
            return (0, [], None, None, False, [], False, "", "")

        skin_count, rare_skins, last_match = self.parse_athena_data(athena_profile)

        common_core = self.fetch_common_core_profile()
        v_bucks = self.parse_common_core_data(common_core) if common_core else 0

        platforms = self.fetch_platforms()
        is_banned, ban_reason = self.fetch_ban_status()

        return (
            skin_count,
            rare_skins,
            v_bucks,
            last_match,
            True,
            platforms,
            is_banned,
            "",
            ban_reason,
        )


async def get_skin_count(page, context=None):
    try:
        api = EpicGamesAPI(page, context)
        return await api.get_all_account_info()
    except Exception:
        return (0, [], None, None, False, [], False, "", "")