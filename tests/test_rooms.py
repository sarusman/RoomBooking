import unittest

from fastapi.testclient import TestClient

import main
from models import room as room_model


class RoomServiceTests(unittest.TestCase):
    def setUp(self):
        self.original_rooms = room_model.rooms.copy()
        self.original_next_id = room_model.next_id
        self.client = TestClient(main.app)

    def tearDown(self):
        self.client.close()
        room_model.rooms = self.original_rooms
        room_model.next_id = self.original_next_id

    def test_health_and_documentation(self):
        self.assertEqual(self.client.get("/health").json(), {"status": "ok"})
        self.assertEqual(self.client.get("/docs").status_code, 200)

    def test_initial_rooms_and_filters(self):
        self.assertEqual(len(self.client.get("/rooms").json()), 3)
        rooms = self.client.get("/rooms?min_capacity=20&available=true").json()
        self.assertEqual([room["name"] for room in rooms], ["A101"])
        rooms = self.client.get("/rooms?available=false").json()
        self.assertEqual([room["name"] for room in rooms], ["C302"])
        self.assertEqual(self.client.get("/rooms?min_capacity=100").json(), [])

    def test_create_read_update_delete(self):
        data = {"name": "D104", "capacity": 12, "floor": 1}
        created = self.client.post("/rooms", json=data)
        self.assertEqual(created.status_code, 201)
        room_id = created.json()["id"]
        url = f"/rooms/{room_id}"
        self.assertEqual(self.client.get(url).json()["name"], "D104")
        data.update(available=False, equipment=["Tableau"], capacity=20)
        updated = self.client.put(url, json=data)
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json(), {**data, "id": room_id})
        deleted = self.client.delete(url)
        self.assertEqual(deleted.status_code, 204)
        self.assertEqual(deleted.content, b"")
        self.assertEqual(self.client.get(url).status_code, 404)
        # Supprimer une salle ne doit pas réutiliser son identifiant.
        self.assertGreater(self.client.post("/rooms", json=data).json()["id"], room_id)

    def test_unknown_room(self):
        for method in ("get", "put", "delete"):
            with self.subTest(method=method):
                kwargs = {"json": {"name": "X", "capacity": 1, "floor": 0}} if method == "put" else {}
                response = getattr(self.client, method)("/rooms/999", **kwargs)
                self.assertEqual(response.status_code, 404)

    def test_invalid_room(self):
        for invalid in ({"capacity": 0}, {"capacity": -1}, {"name": "  "},
                        {"floor": "abc"}, {"id": 42}):
            with self.subTest(invalid=invalid):
                data = {"name": "X", "capacity": 10, "floor": 0, **invalid}
                self.assertEqual(self.client.post("/rooms", json=data).status_code, 422)
        self.assertEqual(self.client.post("/rooms", json={}).status_code, 422)
        self.assertEqual(len(self.client.get("/rooms").json()), 3)

    def test_invalid_update_preserves_room(self):
        original = self.client.get("/rooms/1").json()
        response = self.client.put("/rooms/1", json={"name": "X", "capacity": 0, "floor": 1})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.client.get("/rooms/1").json(), original)

    def test_invalid_filters(self):
        for query in ("min_capacity=0", "min_capacity=abc", "available=abc"):
            with self.subTest(query=query):
                self.assertEqual(self.client.get(f"/rooms?{query}").status_code, 422)


if __name__ == "__main__":
    unittest.main()
