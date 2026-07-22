"""
Desktop OAuth flow for Tauri desktop app.

Flow:
1. Sidecar calls GET /desktop-oauth/start?provider=google
2. Cloud generates state, constructs OAuth URL, returns {ok, state, url}
3. Sidecar opens URL in system browser via webbrowser.open()
4. User authorizes -> OAuth provider redirects to cloud callback
5. Cloud exchanges code for tokens, stores result keyed by state
6. Sidecar polls GET /desktop-oauth/poll?state=xxx until complete
7. Frontend receives tokens, stores in localStorage
"""

import html
import logging
import os
from datetime import datetime, timezone
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import HTMLResponse

from gateway.providers.hub import get_auth_provider, get_data_provider

from .deps import (
    build_user_response,
    mask_email,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _desktop_oauth_provider():
    return get_data_provider().desktop_oauth


def _create_desktop_oauth(provider: str) -> str:
    return _desktop_oauth_provider().create_flow(provider)


def _get_desktop_oauth(state: str) -> dict | None:
    return _desktop_oauth_provider().get_flow(state)


def _complete_desktop_oauth(state: str, result: dict) -> bool:
    return _desktop_oauth_provider().complete_flow(state, result)


def _is_flow_expired(entry: dict) -> bool:
    expires_at = entry.get("expires_at")
    if not expires_at:
        return False
    return expires_at.replace(tzinfo=None) < datetime.now(timezone.utc).replace(tzinfo=None)


_DESKTOP_OAUTH_SUCCESS_HTML = """\
<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Login Successful</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,system-ui,'Segoe UI',sans-serif;display:flex;align-items:center;
justify-content:center;min-height:100vh;background:#08050f;color:#fff;overflow:hidden}}
.bg{{position:fixed;inset:0;z-index:0}}
.bg::before{{content:'';position:absolute;inset:0;
background:radial-gradient(ellipse 80% 60% at 50% 40%,rgba(124,58,237,.15),transparent 70%),
radial-gradient(ellipse 60% 50% at 20% 80%,rgba(139,92,246,.08),transparent),
radial-gradient(ellipse 60% 50% at 80% 20%,rgba(167,139,250,.06),transparent)}}
.orb{{position:absolute;border-radius:50%;filter:blur(80px);animation:float 8s ease-in-out infinite}}
.orb1{{width:300px;height:300px;background:rgba(139,92,246,.12);top:10%;left:15%;animation-delay:0s}}
.orb2{{width:250px;height:250px;background:rgba(124,58,237,.1);bottom:15%;right:10%;animation-delay:-3s}}
.orb3{{width:200px;height:200px;background:rgba(167,139,250,.08);top:50%;left:60%;animation-delay:-5s}}
@keyframes float{{0%,100%{{transform:translateY(0) scale(1)}}50%{{transform:translateY(-30px) scale(1.05)}}}}
.grid{{position:absolute;inset:0;
background-image:linear-gradient(rgba(139,92,246,.03) 1px,transparent 1px),
linear-gradient(90deg,rgba(139,92,246,.03) 1px,transparent 1px);
background-size:60px 60px;mask-image:radial-gradient(ellipse at center,black 30%,transparent 70%)}}
.card{{position:relative;z-index:1;text-align:center;padding:3rem 4rem;border-radius:1.25rem;
background:rgba(139,92,246,.06);border:1px solid rgba(139,92,246,.15);
backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
box-shadow:0 0 60px rgba(139,92,246,.08),inset 0 1px 0 rgba(255,255,255,.05);
animation:cardIn .6s cubic-bezier(.16,1,.3,1) both}}
@keyframes cardIn{{from{{opacity:0;transform:translateY(20px) scale(.96)}}to{{opacity:1;transform:none}}}}
.icon-wrap{{position:relative;width:72px;height:72px;margin:0 auto 1.5rem;animation:iconIn .5s .2s cubic-bezier(.16,1,.3,1) both}}
@keyframes iconIn{{from{{opacity:0;transform:scale(.5)}}to{{opacity:1;transform:none}}}}
.icon-ring{{position:absolute;inset:0;border-radius:50%;border:2px solid rgba(139,92,246,.3);
animation:ringPulse 2s ease-in-out infinite}}
@keyframes ringPulse{{0%,100%{{transform:scale(1);opacity:.6}}50%{{transform:scale(1.15);opacity:0}}}}
.icon-ring2{{position:absolute;inset:-6px;border-radius:50%;border:1px solid rgba(139,92,246,.15);
animation:ringPulse 2s .5s ease-in-out infinite}}
.icon-bg{{position:absolute;inset:0;border-radius:50%;
background:linear-gradient(135deg,rgba(139,92,246,.2),rgba(124,58,237,.1))}}
.icon-check{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center}}
.icon-check svg{{width:32px;height:32px;stroke:#a78bfa;stroke-width:2.5;fill:none;
stroke-linecap:round;stroke-linejoin:round}}
.icon-check svg path{{stroke-dasharray:30;stroke-dashoffset:30;animation:draw .5s .5s ease forwards}}
@keyframes draw{{to{{stroke-dashoffset:0}}}}
h1{{font-size:1.4rem;font-weight:600;margin-bottom:.5rem;
background:linear-gradient(135deg,#e0d4fc,#a78bfa);-webkit-background-clip:text;
-webkit-text-fill-color:transparent;animation:fadeUp .5s .3s cubic-bezier(.16,1,.3,1) both}}
p{{font-size:.9rem;color:rgba(167,139,250,.5);animation:fadeUp .5s .4s cubic-bezier(.16,1,.3,1) both}}
@keyframes fadeUp{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}
.bar{{width:120px;height:3px;margin:1.25rem auto 0;border-radius:2px;background:rgba(139,92,246,.1);
overflow:hidden;animation:fadeUp .5s .5s cubic-bezier(.16,1,.3,1) both}}
.bar-fill{{width:0;height:100%;border-radius:2px;
background:linear-gradient(90deg,#7c3aed,#a78bfa);animation:fill 2.5s .8s ease forwards}}
@keyframes fill{{to{{width:100%}}}}
.particles{{position:fixed;inset:0;z-index:0;overflow:hidden}}
.p{{position:absolute;width:2px;height:2px;background:rgba(167,139,250,.4);border-radius:50%;
animation:rise linear infinite}}
@keyframes rise{{0%{{transform:translateY(100vh) scale(0);opacity:0}}
10%{{opacity:1}}90%{{opacity:1}}100%{{transform:translateY(-10vh) scale(1);opacity:0}}}}
</style></head><body>
<div class="bg"><div class="orb orb1"></div><div class="orb orb2"></div><div class="orb orb3"></div>
<div class="grid"></div></div>
<div class="particles"></div>
<div class="card">
<div class="icon-wrap"><div class="icon-ring"></div><div class="icon-ring2"></div>
<div class="icon-bg"></div>
<div class="icon-check"><svg viewBox="0 0 24 24"><path d="M5 13l4 4L19 7"/></svg></div></div>
<h1>Login Successful</h1><p>Returning to Flyto2...</p>
<div class="bar"><div class="bar-fill"></div></div>
</div>
<script>
(function(){{var c=document.querySelector('.particles');for(var i=0;i<20;i++){{var p=document.createElement('div');
p.className='p';p.style.left=Math.random()*100+'%';p.style.animationDuration=(4+Math.random()*6)+'s';
p.style.animationDelay=Math.random()*5+'s';c.appendChild(p)}}}})();
setTimeout(function(){{window.close();}},2500);
</script></body></html>"""


_DESKTOP_OAUTH_ERROR_HTML = """\
<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Login Failed</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,system-ui,'Segoe UI',sans-serif;display:flex;align-items:center;
justify-content:center;min-height:100vh;background:#08050f;color:#fff;overflow:hidden}}
.bg{{position:fixed;inset:0;z-index:0}}
.bg::before{{content:'';position:absolute;inset:0;
background:radial-gradient(ellipse 80% 60% at 50% 40%,rgba(124,58,237,.12),transparent 70%),
radial-gradient(ellipse 60% 50% at 20% 80%,rgba(139,92,246,.06),transparent)}}
.orb{{position:absolute;border-radius:50%;filter:blur(80px);animation:float 8s ease-in-out infinite}}
.orb1{{width:250px;height:250px;background:rgba(139,92,246,.08);top:20%;left:20%}}
.orb2{{width:200px;height:200px;background:rgba(124,58,237,.06);bottom:20%;right:15%;animation-delay:-3s}}
@keyframes float{{0%,100%{{transform:translateY(0) scale(1)}}50%{{transform:translateY(-20px) scale(1.03)}}}}
.grid{{position:absolute;inset:0;
background-image:linear-gradient(rgba(139,92,246,.03) 1px,transparent 1px),
linear-gradient(90deg,rgba(139,92,246,.03) 1px,transparent 1px);
background-size:60px 60px;mask-image:radial-gradient(ellipse at center,black 30%,transparent 70%)}}
.card{{position:relative;z-index:1;text-align:center;padding:3rem 4rem;border-radius:1.25rem;
background:rgba(139,92,246,.04);border:1px solid rgba(139,92,246,.12);
backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
box-shadow:0 0 40px rgba(139,92,246,.06),inset 0 1px 0 rgba(255,255,255,.04);
animation:cardIn .6s cubic-bezier(.16,1,.3,1) both}}
@keyframes cardIn{{from{{opacity:0;transform:translateY(20px) scale(.96)}}to{{opacity:1;transform:none}}}}
.icon-wrap{{position:relative;width:72px;height:72px;margin:0 auto 1.5rem;animation:iconIn .5s .2s cubic-bezier(.16,1,.3,1) both}}
@keyframes iconIn{{from{{opacity:0;transform:scale(.5)}}to{{opacity:1;transform:none}}}}
.icon-bg{{position:absolute;inset:0;border-radius:50%;
background:linear-gradient(135deg,rgba(239,68,68,.15),rgba(220,38,38,.08))}}
.icon-x{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center}}
.icon-x svg{{width:28px;height:28px;stroke:#f87171;stroke-width:2.5;fill:none;
stroke-linecap:round}}
.icon-x svg line{{stroke-dasharray:20;stroke-dashoffset:20;animation:draw .4s .4s ease forwards}}
@keyframes draw{{to{{stroke-dashoffset:0}}}}
h1{{font-size:1.4rem;font-weight:600;margin-bottom:.5rem;color:#fca5a5;
animation:fadeUp .5s .3s cubic-bezier(.16,1,.3,1) both}}
p{{font-size:.85rem;color:rgba(167,139,250,.45);max-width:280px;line-height:1.5;
animation:fadeUp .5s .4s cubic-bezier(.16,1,.3,1) both}}
@keyframes fadeUp{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}
.retry{{display:inline-block;margin-top:1.25rem;padding:.5rem 1.5rem;border-radius:.5rem;
font-size:.85rem;color:#c4b5fd;background:rgba(139,92,246,.1);border:1px solid rgba(139,92,246,.2);
cursor:pointer;text-decoration:none;transition:all .2s;animation:fadeUp .5s .5s cubic-bezier(.16,1,.3,1) both}}
.retry:hover{{background:rgba(139,92,246,.18);border-color:rgba(139,92,246,.35);transform:translateY(-1px)}}
</style></head><body>
<div class="bg"><div class="orb orb1"></div><div class="orb orb2"></div><div class="grid"></div></div>
<div class="card">
<div class="icon-wrap"><div class="icon-bg"></div>
<div class="icon-x"><svg viewBox="0 0 24 24"><line x1="7" y1="7" x2="17" y2="17"/><line x1="17" y1="7" x2="7" y2="17"/></svg></div></div>
<h1>Login Failed</h1><p>{error}</p>
<a class="retry" onclick="window.close()">Close Window</a>
</div></body></html>"""


def _build_callback_url(request: Request) -> str:
    """Derive the public callback URL from request headers."""
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host_ = request.headers.get("host", request.url.netloc)
    return f"{scheme}://{host_}/api/auth/desktop-oauth/callback"


@router.get("/desktop-oauth/start")
async def desktop_oauth_start(request: Request, provider: str = Query(...)):
    """
    Start a desktop OAuth flow. Called by the local sidecar.

    Generates a state token, constructs the OAuth provider URL,
    and returns it so the sidecar can open it in the system browser.
    """
    if provider not in ("google", "github"):
        return {"ok": False, "error": f"Unsupported provider: {provider}"}

    callback_url = _build_callback_url(request)
    state = _create_desktop_oauth(provider)

    if provider == "google":
        client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "")
        if not client_id:
            return {"ok": False, "error": "Google OAuth not configured"}

        params = urlencode({
            "client_id": client_id,
            "redirect_uri": callback_url,
            "response_type": "code",
            "scope": "email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "select_account",
        })
        url = f"https://accounts.google.com/o/oauth2/v2/auth?{params}"

    else:  # github
        client_id = os.environ.get("GITHUB_CLIENT_ID", "")
        if not client_id:
            return {"ok": False, "error": "GitHub OAuth not configured"}

        params = urlencode({
            "client_id": client_id,
            "redirect_uri": callback_url,
            "state": state,
            "scope": "user:email",
        })
        url = f"https://github.com/login/oauth/authorize?{params}"

    return {"ok": True, "state": state, "url": url}


@router.get("/desktop-oauth/callback")
async def desktop_oauth_callback(
    request: Request,
    state: str = Query(default=""),
    code: str = Query(default=""),
    error_param: str = Query(default="", alias="error"),
):
    """
    OAuth callback from provider (Google/GitHub).

    The user's system browser is redirected here after authorization.
    Exchanges the code for tokens, stores the result, and shows a
    success/error HTML page.
    """
    if error_param:
        if state:
            _complete_desktop_oauth(state, {
                "status": "complete", "ok": False,
                "error": f"OAuth denied: {error_param}",
            })
        safe_error = html.escape(error_param)
        return HTMLResponse(_DESKTOP_OAUTH_ERROR_HTML.format(error=safe_error))

    if not state or not code:
        return HTMLResponse(
            _DESKTOP_OAUTH_ERROR_HTML.format(error="Missing state or code parameter"),
            status_code=400,
        )

    entry = _get_desktop_oauth(state)
    if not entry:
        return HTMLResponse(
            _DESKTOP_OAUTH_ERROR_HTML.format(error="Invalid or expired OAuth session"),
            status_code=400,
        )

    if entry["status"] != "pending":
        return HTMLResponse(
            _DESKTOP_OAUTH_ERROR_HTML.format(error="OAuth session already used"),
            status_code=400,
        )

    provider = entry["provider"]
    callback_url = _build_callback_url(request)

    try:
        auth_prov = get_auth_provider()
        firebase_result = await auth_prov.exchange_desktop_oauth_code(
            provider,
            code=code,
            redirect_uri=callback_url,
        )

        # Build user response (reuses helpers from social.py)
        from api.auth.social import _ensure_user_doc, _build_user_dict

        user_id = firebase_result.get("localId")
        email = firebase_result.get("email", "")
        display_name = firebase_result.get("displayName", "")
        photo_url = firebase_result.get("photoUrl", "")
        screen_name = firebase_result.get("screenName", "")
        is_new_user = firebase_result.get("isNewUser", False)
        username_hint = screen_name or (email.split("@")[0] if email else "")

        user_data = await _ensure_user_doc(
            auth_prov, user_id=user_id, email=email,
            display_name=display_name or screen_name or username_hint,
            photo_url=photo_url, is_new_user=is_new_user, username_hint=username_hint,
            masked=mask_email(email), provider_label=f"{provider} (desktop)",
        )
        user_dict = _build_user_dict(user_id, email, display_name, photo_url, username_hint, user_data)

        _complete_desktop_oauth(state, {
            "status": "complete",
            "ok": True,
            "access_token": firebase_result.get("idToken"),
            "refresh_token": firebase_result.get("refreshToken"),
            "user": build_user_response(user_dict),
        })

        return HTMLResponse(_DESKTOP_OAUTH_SUCCESS_HTML)

    except Exception:
        logger.exception("Desktop OAuth callback failed")
        _complete_desktop_oauth(state, {
            "status": "complete", "ok": False, "error": "Authentication failed",
        })
        return HTMLResponse(
            _DESKTOP_OAUTH_ERROR_HTML.format(error="Authentication failed. Please try again."),
            status_code=500,
        )


@router.get("/desktop-oauth/poll")
async def desktop_oauth_poll(state: str = Query(...)):
    """
    Poll for desktop OAuth result. Called by the sidecar.

    Returns:
    - {status: "pending"} -- user hasn't completed OAuth yet
    - {status: "complete", ok, access_token, refresh_token, user} -- success
    - {status: "complete", ok: false, error} -- failed
    - {status: "expired"} -- flow timed out
    - {status: "not_found"} -- unknown state
    """
    entry = _get_desktop_oauth(state)
    if not entry:
        return {"status": "not_found"}

    if _is_flow_expired(entry):
        return {"status": "expired"}

    if entry["status"] == "pending":
        return {"status": "pending"}

    return entry["result"]


@router.get("/provider")
async def get_auth_provider_info():
    """Get current auth provider info (for debugging)."""
    auth_provider = get_auth_provider()
    return {
        "provider": auth_provider.provider_name
    }


@router.get("/languages")
async def get_available_languages():
    """
    Get available languages from i18n CDN manifest.

    Returns list of locale codes with metadata (name, native name, completion).
    Used by admin panel for configuring user language permissions.
    """
    import httpx

    cdn_urls = [
        "https://cdn.jsdelivr.net/gh/flytohub/flyto-i18n@main/dist/manifest.json",
    ]

    for url in cdn_urls:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    manifest = response.json()
                    locales = manifest.get("locales", {})

                    # Convert to list format for frontend
                    languages = []
                    for code, info in locales.items():
                        languages.append({
                            "code": code,
                            "name": info.get("name", code),
                            "native": info.get("native", code),
                            "region": info.get("region", code[:2].upper()),
                            "completion": info.get("completion", 0),
                        })

                    return {
                        "ok": True,
                        "languages": languages,
                        "total": len(languages),
                    }
        except Exception as e:
            logger.warning(f"Failed to fetch manifest from {url}: {e}")
            continue

    # Fallback if all CDN endpoints fail
    return {
        "ok": True,
        "languages": [
            {"code": "en", "name": "English", "native": "English", "region": "US", "completion": 100},
        ],
        "total": 1,
    }
