"""Export every slide deck that asks for it (its PDF menu carries data-pdf-files) to two PDF files next to it:
    <course>-session-NN-slides.pdf   one slide per 16:9 page   (the deck's ?print-pdf view)
    <course>-session-NN-handout.pdf  two slides per A4 page    (the deck's ?handout view)
Chrome (Playwright) prints them, so a phone downloads exactly the pages a desktop prints — phone browsers ignore the
page size a web page asks for. Run by .github/workflows/deploy.yml on the assembled site (master at / and cv-next under /dev/):
    python3 export_pdfs.py site
A deck that fails is reported and skipped; the deck's menu then keeps its live print pages.
"""
import asyncio, glob, http.server, os, re, socketserver, sys, threading, functools, time
from playwright.async_api import async_playwright

ROOT = os.path.abspath(sys.argv[1])
PORT = 8765


def decks():
    for p in sorted(glob.glob(f"{ROOT}/**/session-*/slides.html", recursive=True)):
        with open(p, encoding="utf-8", errors="ignore") as f:
            if "data-pdf-files" in f.read():
                yield p


def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    handler = functools.partial(Quiet, directory=ROOT)
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


async def main():
    found = list(decks())
    print(f"{len(found)} deck(s) to export")
    failed = 0
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for path in found:
            rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
            m = re.search(r"([^/]+)/(session-\d+)/slides\.html$", rel)
            base = f"{m.group(1)}-{m.group(2)}"
            for kind, query, opts in (("slides", "print-pdf", {}), ("handout", "handout", {"format": "A4"})):
                out = os.path.join(os.path.dirname(path), f"{base}-{kind}.pdf")
                t0 = time.time()
                try:
                    q = await b.new_page(viewport={"width": 1280, "height": 720})
                    await q.goto(f"http://127.0.0.1:{PORT}/{rel}?{query}", wait_until="load", timeout=90000)
                    await q.wait_for_function("document.documentElement.dataset.printReady==='1'", timeout=90000)
                    await q.wait_for_timeout(800)
                    await q.pdf(path=out, print_background=True, prefer_css_page_size=True, **opts)
                    await q.close()
                    print(f"  {rel} → {os.path.basename(out)} · {os.path.getsize(out) / 1e6:.1f} MB · {time.time() - t0:.0f}s")
                except Exception as e:   # one deck must not stop the others, nor the deploy
                    failed += 1
                    if os.path.exists(out):
                        os.remove(out)
                    print(f"::warning::PDF export failed for {rel} ({kind}): {str(e)[:300]}")
        await b.close()
    print(f"done · {failed} failed")


httpd = serve()
try:
    asyncio.run(main())
finally:
    httpd.shutdown()
