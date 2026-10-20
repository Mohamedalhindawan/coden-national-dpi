from playwright.sync_api import sync_playwright

AXE = "/tmp/a11y/node_modules/axe-core/axe.min.js"
URL = "file:///workspace/chats/bc4b0bd025fbde0c4eaa2054/app/index.html"
SHOTS = "/workspace/chats/bc4b0bd025fbde0c4eaa2054/artifacts"

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))


def run_axe(page, label):
    page.add_script_tag(path=AXE)
    res = page.evaluate(
        "async () => await axe.run(document, { runOnly: { type: 'tag', values: "
        "['wcag2a','wcag2aa','wcag21a','wcag21aa','best-practice'] } })"
    )
    ids = [v["id"] for v in res["violations"]]
    check(f"axe 0 violations ({label})", not ids, ", ".join(ids))
    return res


with sync_playwright() as p:
    browser = p.chromium.launch(args=["--no-sandbox"])

    # --- JavaScript disabled ---
    ctx = browser.new_context(java_script_enabled=False, viewport={"width": 390, "height": 844})
    page = ctx.new_page()
    page.goto(URL)
    check("noscript message shown when JS is off", page.locator("noscript").is_visible())
    text = page.inner_text("noscript")
    check("noscript message is Arabic", "يحتاج هذا النموذج إلى JavaScript" in text, text[:80])
    check("name field disabled", not page.is_enabled("#fullName"))
    check("district disabled", not page.is_enabled("#district"))
    check("size disabled", not page.is_enabled("#householdSize"))
    check("need type disabled", not page.is_enabled("#needType"))
    check("submit disabled", not page.is_enabled("#submitRequest"))
    try:
        page.click("#submitRequest", timeout=1500)
        submitted = True
    except Exception:
        submitted = False
    check("submit cannot be triggered", not submitted)
    check("URL unchanged, no query data", "?" not in page.url, page.url)
    try:
        run_axe(page, "JS off, mobile")
    except Exception as exc:
        results.append(("axe 0 violations (JS off, mobile)", None, f"not runnable: {exc}"))
    page.screenshot(path=f"{SHOTS}/tamam-nojs.png", full_page=True)
    ctx.close()

    # --- JavaScript enabled: full flow + accessibility ---
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.goto(URL)
    check("noscript hidden when JS is on", not page.locator("noscript").is_visible())
    check("controls enabled when JS is on", page.is_enabled("#fullName") and page.is_enabled("#submitRequest"))
    run_axe(page, "desktop, default state")

    page.fill("#fullName", "أسرة تجريبية 010")
    page.select_option("#district", index=1)
    page.fill("#householdSize", "4")
    page.select_option("#needType", "food")
    page.click("#submitRequest")
    check("request added", page.locator("#requests article").count() == 1)
    check("success announced", "تمت إضافة الطلب التجريبي" in page.inner_text("#feedback"))
    page.get_by_role("button", name="تسجيل مراجعة تجريبية للطلب DEMO-001").click()
    check("review recorded", "تمت مراجعة تجريبية" in page.inner_text("#requests"))
    run_axe(page, "desktop, filled and reviewed state")
    page.click("#clearRequests")
    check("session cleared", "تم مسح جميع الطلبات التجريبية" in page.inner_text("#feedback"))
    check("no console or page errors", not errors, "; ".join(errors))
    browser.close()

failed = [r for r in results if r[1] is False]
skipped = [r for r in results if r[1] is None]
for name, ok, detail in results:
    mark = "PASS " if ok else ("SKIP " if ok is None else "FAIL ")
    print(mark + name + (f" ({detail})" if detail and ok is not True else ""))
print(f"\n{len(results) - len(failed) - len(skipped)} passed, {len(failed)} failed, {len(skipped)} not runnable")
raise SystemExit(1 if failed else 0)
