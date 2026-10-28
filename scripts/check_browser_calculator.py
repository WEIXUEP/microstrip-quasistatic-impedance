"""Run opt-in browser regression checks against a prepared site."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--channel', default=None, help='Playwright browser channel, for example msedge')
    args = parser.parse_args()
    handler = partial(SimpleHTTPRequestHandler, directory=str(ROOT / 'site'))
    server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel=args.channel, headless=True)
            page = browser.new_page(viewport={'width': 390, 'height': 844}, accept_downloads=True)
            page.goto(f'http://127.0.0.1:{server.server_port}/calculator/', wait_until='domcontentloaded')
            page.wait_for_function('crossOriginIsolated', timeout=30000)

            def calculate(expected):
                page.locator('#run').click()
                page.wait_for_function("document.querySelector('#status').textContent.includes('complete') || document.querySelector('#status').classList.contains('error')", timeout=180000)
                status = page.locator('#status').inner_text()
                if status != 'Calculation complete.':
                    raise AssertionError(status)
                actual = float(page.locator('#impedance').inner_text())
                if abs(actual - expected) > 0.002:
                    raise AssertionError(f'Impedance {actual} differs from {expected}')
                print(f'Impedance {actual:.4f} ohm')

            calculate(31.55849811)
            page.locator('[name=er1]').fill('1')
            page.locator('[name=er2]').fill('1')
            calculate(61.65455342)
            assert float(page.locator('#eeff').inner_text()) == 1.0
            with page.expect_download() as download:
                page.locator('#download').click()
            assert download.value.suggested_filename == 'microstrip-result.json'
            for key, value in {'h1':'5', 'h2':'5', 'w1':'20', 'w2':'50', 'trace_thickness':'1', 'er1':'3.66', 'er2':'4.2'}.items():
                page.locator(f'[name={key}]').fill(value)
            calculate(16.37577408)
            assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
            page.locator('[name=trace_thickness]').fill('5')
            page.locator('#run').click()
            assert 'smaller' in page.locator('#status').inner_text()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()

if __name__ == '__main__':
    main()
