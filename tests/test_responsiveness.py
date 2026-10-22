"""
Automated Responsiveness and Mobile Viewport Tests
Validates viewport meta tags, responsive CSS media queries, and mobile drawer controls.
"""

import os
import sys
import unittest

_current_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_current_dir)
_src_dir = os.path.join(_root_dir, "src")
for _p in [_src_dir, _root_dir]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app import app


class TestMobileResponsiveness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        cls.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.index_path = os.path.join(cls.base_dir, "src", "templates", "index.html")
        cls.analytics_path = os.path.join(cls.base_dir, "src", "templates", "analytics.html")
        cls.css_path = os.path.join(cls.base_dir, "src", "static", "css", "style.css")
        cls.js_path = os.path.join(cls.base_dir, "src", "static", "js", "main.js")

    def test_viewport_meta_tag_index_html(self):
        """TC-RESP-01: Verify viewport meta tag exists and is correct in index.html"""
        with open(self.index_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn('<meta name="viewport" content="width=device-width, initial-scale=1.0">', content)

    def test_viewport_meta_tag_analytics_html(self):
        """TC-RESP-02: Verify viewport meta tag exists and is correct in analytics.html"""
        with open(self.analytics_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn('<meta name="viewport" content="width=device-width, initial-scale=1.0">', content)

    def test_mobile_drawer_elements_in_html(self):
        """TC-RESP-03: Verify mobile sidebar toggle, close button, and backdrop exist in index.html"""
        with open(self.index_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn('id="sidebarToggleBtn"', content)
        self.assertIn('id="sidebarCloseBtn"', content)
        self.assertIn('id="sidebarBackdrop"', content)
        self.assertIn('id="sidebar"', content)

    def test_mobile_drawer_js_handlers(self):
        """TC-RESP-04: Verify main.js contains event listeners for mobile drawer"""
        with open(self.js_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("sidebarToggleBtn", content)
        self.assertIn("sidebarCloseBtn", content)
        self.assertIn("sidebarBackdrop", content)
        self.assertIn("openSidebar", content)
        self.assertIn("closeSidebar", content)

    def test_css_responsive_media_queries(self):
        """TC-RESP-05: Verify style.css includes media queries covering tablet, mobile, and ultra-compact viewports"""
        with open(self.css_path, "r", encoding="utf-8") as f:
            css = f.read()
        self.assertIn("@media (max-width: 900px)", css)
        self.assertIn("@media (max-width: 640px)", css)
        self.assertIn("@media (max-width: 390px)", css)
        self.assertIn("@media (max-width: 340px)", css)
        self.assertIn("translateX(-105%)", css)
        self.assertIn(".sidebar.open", css)
        self.assertIn(".sidebar-backdrop", css)

    def test_prevent_ios_input_zoom(self):
        """TC-RESP-06: Verify textarea font-size is at least 16px (1rem) to prevent iOS auto-zoom on focus"""
        with open(self.css_path, "r", encoding="utf-8") as f:
            css = f.read()
        self.assertIn("font-size: 1rem", css)
        self.assertIn("font-size: 16px", css)

    def test_flask_endpoints_serve_updated_assets(self):
        """TC-RESP-07: Verify Flask serves index, CSS, and JS successfully"""
        r_index = self.client.get("/")
        self.assertEqual(r_index.status_code, 200)
        self.assertIn(b"sidebarToggleBtn", r_index.data)

        r_css = self.client.get("/style.css")
        self.assertEqual(r_css.status_code, 200)
        self.assertIn(b"@media (max-width: 900px)", r_css.data)

        r_js = self.client.get("/script.js")
        self.assertEqual(r_js.status_code, 200)
        self.assertIn(b"sidebarToggleBtn", r_js.data)


if __name__ == "__main__":
    unittest.main()
