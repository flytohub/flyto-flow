"""Build-time smoke for the exact flyto-core browser.launch path."""

from __future__ import annotations

import asyncio

from core.modules.atomic.browser.launch import BrowserLaunchModule


async def main() -> None:
    context = {}
    module = BrowserLaunchModule(
        params={"headless": False, "browser_type": "chromium", "stealth": False},
        context=context,
    )
    if module.headless is not True:
        raise RuntimeError("Container browser.launch must force headless mode")

    result = await module.execute()
    try:
        if result.get("status") != "success":
            raise RuntimeError(f"browser.launch smoke failed: {result}")
    finally:
        browser = context.get("browser")
        if browser is not None:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
