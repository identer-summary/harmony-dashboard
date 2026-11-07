import unittest

from dashboard import app, reports_db


class DashboardRoutesTest(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_dashboard_renders(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Harmony Watcher".encode(), response.data)

    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})

    def test_data_endpoint(self):
        response = self.client.get("/api/data")
        self.assertEqual(response.status_code, 200)
        self.assertIn("202-503", response.get_json())

    def test_report_status_is_calculated(self):
        response = self.client.post(
            "/api/report",
            json={
                "building": "202",
                "unit": "303",
                "avgNoise": 51,
                "maxNoise": 72,
                "vibration": 0.0018,
                "frequency": 130,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["report"]["status"], "심각")
        reports_db.pop("202-303", None)

    def test_invalid_report_is_rejected(self):
        response = self.client.post("/api/report", data="not-json")
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
