import unittest

from app import app


class ApplicationSmokeTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health(self):
        self.assertEqual(self.client.get("/health").json, {"status": "ok"})

    def test_search_returns_seeded_user(self):
        result = self.client.get("/api/users?q=alice")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json["users"][0][1], "alice")

    def test_home_exposes_crawlable_links(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"/search?q=alice", response.data)


if __name__ == "__main__":
    unittest.main()
