def test_create_lead_returns_201_with_id_and_timestamp(client, lead_payload):
    r = client.post("/api/leads", json=lead_payload)
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1
    assert body["created_at"]
    assert {k: body[k] for k in lead_payload} == lead_payload


def test_status_defaults_to_new(client):
    r = client.post("/api/leads", json={"name": "Bob", "company": "Globex", "region": "NA"})
    assert r.status_code == 201
    assert r.json()["status"] == "new"


def test_list_returns_all_leads_newest_first(client, lead_payload):
    client.post("/api/leads", json=lead_payload)
    client.post("/api/leads", json={**lead_payload, "name": "Bob"})
    names = [lead["name"] for lead in client.get("/api/leads").json()]
    assert names == ["Bob", "Ada Lovelace"]


def test_list_is_empty_initially(client):
    assert client.get("/api/leads").json() == []


def test_filter_by_status(client, lead_payload):
    client.post("/api/leads", json=lead_payload)  # qualified
    client.post("/api/leads", json={**lead_payload, "name": "Bob", "status": "won"})
    client.post("/api/leads", json={**lead_payload, "name": "Cy", "status": "new"})

    qualified = client.get("/api/leads", params={"status": "qualified"}).json()
    assert [lead["name"] for lead in qualified] == ["Ada Lovelace"]

    assert client.get("/api/leads", params={"status": "lost"}).json() == []


def test_filter_with_invalid_status_is_422(client):
    assert client.get("/api/leads", params={"status": "bogus"}).status_code == 422


def test_create_with_invalid_status_is_422(client, lead_payload):
    r = client.post("/api/leads", json={**lead_payload, "status": "maybe"})
    assert r.status_code == 422


def test_create_with_blank_name_is_422(client, lead_payload):
    r = client.post("/api/leads", json={**lead_payload, "name": ""})
    assert r.status_code == 422


def test_create_with_missing_field_is_422(client):
    r = client.post("/api/leads", json={"name": "Ada", "company": "Acme"})
    assert r.status_code == 422


def test_get_single_lead(client, lead_payload):
    created = client.post("/api/leads", json=lead_payload).json()
    r = client.get(f"/api/leads/{created['id']}")
    assert r.status_code == 200
    assert r.json() == created


def test_get_missing_lead_is_404(client):
    r = client.get("/api/leads/999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Lead not found"


def test_update_status(client, lead_payload):
    created = client.post("/api/leads", json=lead_payload).json()
    r = client.patch(f"/api/leads/{created['id']}", json={"status": "won"})
    assert r.status_code == 200
    assert r.json() == {**created, "status": "won"}
    assert client.get(f"/api/leads/{created['id']}").json()["status"] == "won"


def test_update_status_on_missing_lead_is_404(client):
    r = client.patch("/api/leads/999", json={"status": "won"})
    assert r.status_code == 404
    assert r.json()["detail"] == "Lead not found"


def test_update_with_invalid_status_is_422(client, lead_payload):
    created = client.post("/api/leads", json=lead_payload).json()
    r = client.patch(f"/api/leads/{created['id']}", json={"status": "maybe"})
    assert r.status_code == 422
    assert client.get(f"/api/leads/{created['id']}").json()["status"] == "qualified"


def test_update_with_missing_status_is_422(client, lead_payload):
    created = client.post("/api/leads", json=lead_payload).json()
    assert client.patch(f"/api/leads/{created['id']}", json={}).status_code == 422


def test_delete_lead(client, lead_payload):
    created = client.post("/api/leads", json=lead_payload).json()
    r = client.delete(f"/api/leads/{created['id']}")
    assert r.status_code == 204
    assert r.content == b""
    assert client.get(f"/api/leads/{created['id']}").status_code == 404
    assert client.get("/api/leads").json() == []


def test_delete_only_removes_target_lead(client, lead_payload):
    first = client.post("/api/leads", json=lead_payload).json()
    client.post("/api/leads", json={**lead_payload, "name": "Bob"})
    client.delete(f"/api/leads/{first['id']}")
    assert [lead["name"] for lead in client.get("/api/leads").json()] == ["Bob"]


def test_delete_missing_lead_is_404(client):
    r = client.delete("/api/leads/999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Lead not found"
