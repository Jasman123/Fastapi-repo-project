from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from app.core.config import get_settings
from app.core.logging import get_logger


logger = get_logger(__name__)

async def fetch_page_text(url: str) -> tuple[str, str | None] :
    settings = get_settings()
    combined_text=""
    error = None

    paths_to_try = ["", "/about", "/about-us", "/contact"]

    try:
        async with async_playwright as p:
            browser = await p.chromium.lauch(
                headless=settings.PLAYWRIGHT_HEADLESS,
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "heigth": 800}
            )

            page = await context.new_page()
            seen_lines: set[str] = set()

            for path in paths_to_try:
                target_url = url.rstrip("/") + path
                try:
                    await page.goto(
                        target_url,
                        timeout=settings.PLAYWRIGHT_TIMEOUT_MS,
                        wait_util="domcontentloaded",
                    )

                    raw = await page.evaluate("""() => {
                        const walker = document.createTreeWalker(
                            document.body,
                            NodeFilter.SHOW_TEXT,
                            null
                        );
                        const texts = [];
                        let node;
                        while (node = walker.nextNode()) {
                            const parent = node.parentElement;
                            if (!parent) continue;
                            const style = window.getComputedStyle(parent);
                            if (style.display === 'none' || style.visibility === 'hidden')
                                continue;
                            const text = node.textContent.trim();
                            if (text.length > 20) texts.push(text);
                        }
                        return texts.join('\\n');
                    }""")

                    for line in raw.split("\n"):
                        clean = line.strip()
                        if clean and clean not in seen_lines:
                            seen_lines.add(clean)
                    
                    logger.debug(f"Fetched {target_url} - {len(raw)} chars")
                
                except PlaywrightTimeout:
                    logger.debug(f"Timeout on {target_url} — skipping")
                    continue
                except Exception as e:
                    logger.debug(f"Error on {target_url}: {e} — skipping")
                    continue

            await browser.close()
        
    except Exception as e:
        error = f"Playwright failed for {url}: {str(e)}"
        logger.error(error)
        return "", error
    
    if not combined_text.strip():
        error = f"No text extracted from {url} — may be heavily JS-rendered or blocked"
        logger.warning(error)
        return "", error
    
    logger.info(f"Scraped {url} — {len(combined_text)} chars total")
    return combined_text[:8000], None  # cap at 8k chars to fit LLM context
                    