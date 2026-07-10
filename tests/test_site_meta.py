#!/usr/bin/env python3
"""Every published page must unfurl.

Sharing a link with no Open Graph tags produces a bare-text preview, and an og:image
that is the wrong size (or an animated GIF) gets silently downgraded to a small card.
Both failures are invisible locally — you only find out after you've posted the link.
So they get a test.
"""
import re
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
BASE = "https://kumarsashank.github.io/motiscope"

REQUIRED = ["og:title", "og:description", "og:url", "og:image",
            "og:image:width", "og:image:height", "og:image:alt"]
REQUIRED_TW = ["twitter:card", "twitter:image"]

# Pages that are meant to be shared. Fragment/asset pages are exempt.
PAGES = ["index.html", "gallery.html", "how-it-works.html",
         "examples/ambient/index.html", "examples/parallax/index.html",
         "examples/basics/index.html", "examples/landing/index.html"]


def meta(html: str) -> dict:
    out = {}
    for m in re.finditer(r'<meta\s+(property|name)="([^"]+)"\s+content="([^"]*)"', html):
        out[m.group(2)] = m.group(3)
    return out


def png_size(path: Path):
    """Width/height straight out of the PNG IHDR — no third-party imports."""
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", f"{path} is not a PNG"
    w, h = struct.unpack(">II", data[16:24])
    return w, h


class TestSocialPreview(unittest.TestCase):
    def test_every_shared_page_has_the_required_tags(self):
        for page in PAGES:
            m = meta((DOCS / page).read_text())
            for tag in REQUIRED + REQUIRED_TW:
                with self.subTest(page=page, tag=tag):
                    self.assertIn(tag, m, f"{page} is missing <meta {tag}>")

    def test_twitter_card_is_large(self):
        for page in PAGES:
            m = meta((DOCS / page).read_text())
            with self.subTest(page=page):
                self.assertEqual(m["twitter:card"], "summary_large_image")

    def test_og_image_is_a_real_1200x630_png(self):
        for page in PAGES:
            m = meta((DOCS / page).read_text())
            url = m["og:image"]
            with self.subTest(page=page):
                self.assertTrue(url.startswith(BASE + "/"),
                                f"{page}: og:image must be an absolute URL on the site, got {url}")
                local = DOCS / url[len(BASE) + 1:]
                self.assertTrue(local.is_file(), f"{page}: og:image {url} has no file at {local}")
                self.assertEqual(png_size(local), (1200, 630),
                                 f"{page}: og:image must be 1200x630")
                self.assertEqual(m["og:image:width"], "1200")
                self.assertEqual(m["og:image:height"], "630")
                # unfurlers refuse very large images; keep them lean
                self.assertLess(local.stat().st_size, 1_000_000,
                                f"{page}: og:image is over 1 MB")

    def test_og_url_points_at_the_page_itself(self):
        expected = {
            "index.html": f"{BASE}/",
            "gallery.html": f"{BASE}/gallery.html",
            "how-it-works.html": f"{BASE}/how-it-works.html",
            "examples/ambient/index.html": f"{BASE}/examples/ambient/",
            "examples/parallax/index.html": f"{BASE}/examples/parallax/",
            "examples/basics/index.html": f"{BASE}/examples/basics/",
            "examples/landing/index.html": f"{BASE}/examples/landing/",
        }
        for page, url in expected.items():
            m = meta((DOCS / page).read_text())
            with self.subTest(page=page):
                self.assertEqual(m["og:url"], url)

    def test_descriptions_survive_truncation(self):
        for page in PAGES:
            m = meta((DOCS / page).read_text())
            with self.subTest(page=page):
                d = m["og:description"]
                self.assertGreater(len(d), 60, f"{page}: og:description is too thin")
                self.assertLess(len(d), 300, f"{page}: og:description will be truncated hard")

    def test_no_animated_gif_is_used_as_a_card(self):
        for page in PAGES:
            m = meta((DOCS / page).read_text())
            with self.subTest(page=page):
                self.assertFalse(m["og:image"].endswith(".gif"),
                                 f"{page}: an animated GIF card gets downgraded by most unfurlers")

    def test_cards_are_not_hotlinked_from_raw_githubusercontent(self):
        """Serve cards from the Pages origin: raw.githubusercontent is not a CDN for this."""
        for page in PAGES:
            m = meta((DOCS / page).read_text())
            with self.subTest(page=page):
                self.assertNotIn("raw.githubusercontent.com", m["og:image"])


class TestSearchIndexing(unittest.TestCase):
    """A page nobody can find is a page nobody reads."""

    def test_robots_allows_everything_and_names_the_sitemap(self):
        robots = (DOCS / "robots.txt").read_text()
        self.assertIn("Allow: /", robots)
        self.assertNotIn("Disallow: /\n", robots)
        self.assertIn(f"Sitemap: {BASE}/sitemap.xml", robots)

    def test_sitemap_lists_every_published_page(self):
        sm = (DOCS / "sitemap.xml").read_text()
        expected = {
            f"{BASE}/",
            f"{BASE}/gallery.html",
            f"{BASE}/how-it-works.html",
            f"{BASE}/examples/ambient/",
            f"{BASE}/examples/parallax/",
            f"{BASE}/examples/basics/",
            f"{BASE}/examples/landing/",
        }
        for loc in expected:
            with self.subTest(url=loc):
                self.assertIn(f"<loc>{loc}</loc>", sm,
                              f"{loc} is published but absent from sitemap.xml")

    def test_sitemap_urls_resolve_to_real_files(self):
        sm = (DOCS / "sitemap.xml").read_text()
        for loc in re.findall(r"<loc>([^<]+)</loc>", sm):
            with self.subTest(url=loc):
                rel = loc[len(BASE) + 1:] or "index.html"
                if rel.endswith("/"):
                    rel += "index.html"
                self.assertTrue((DOCS / rel).is_file(), f"sitemap points at missing {rel}")

    def test_homepage_declares_structured_data(self):
        import json
        html = (DOCS / "index.html").read_text()
        m = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
        self.assertIsNotNone(m, "index.html has no JSON-LD; search engines get no entity")
        graph = json.loads(m.group(1))["@graph"]
        types = {n["@type"] for n in graph}
        self.assertIn("SoftwareApplication", types)
        self.assertIn("SoftwareSourceCode", types)


if __name__ == "__main__":
    unittest.main()
