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


def test_search_by_company_is_partial_and_case_insensitive(client, lead_payload):
    client.post("/api/leads", json={**lead_payload, "company": "Acme Corp"})
    client.post("/api/leads", json={**lead_payload, "name": "Bob", "company": "Globex"})
    client.post("/api/leads", json={**lead_payload, "name": "Cy", "company": "ACME Labs"})

    r = client.get("/api/leads/search", params={"company": "acme"})
    assert r.status_code == 200
    assert [lead["name"] for lead in r.json()] == ["Cy", "Ada Lovelace"]


def test_search_with_no_match_returns_empty_list(client, lead_payload):
    client.post("/api/leads", json=lead_payload)
    r = client.get("/api/leads/search", params={"company": "Initech"})
    assert r.status_code == 200
    assert r.json() == []


def test_search_treats_like_wildcards_literally(client, lead_payload):
    client.post("/api/leads", json={**lead_payload, "company": "100% Co"})
    client.post("/api/leads", json={**lead_payload, "name": "Bob", "company": "Acme"})
    client.post("/api/leads", json={**lead_payload, "name": "Cy", "company": "Foo_Bar"})

    assert [l["name"] for l in client.get("/api/leads/search", params={"company": "%"}).json()] == ["Ada Lovelace"]
    assert [l["name"] for l in client.get("/api/leads/search", params={"company": "_"}).json()] == ["Cy"]


def test_search_does_not_modify_leads(client, lead_payload):
    client.post("/api/leads", json=lead_payload)
    client.post("/api/leads", json={**lead_payload, "name": "Bob", "company": "Globex"})
    before = client.get("/api/leads").json()
    client.get("/api/leads/search", params={"company": "Acme"})
    assert client.get("/api/leads").json() == before


def test_search_without_company_is_422(client):
    assert client.get("/api/leads/search").status_code == 422


def test_search_with_blank_company_is_422(client):
    assert client.get("/api/leads/search", params={"company": ""}).status_code == 422
    assert client.get("/api/leads/search", params={"company": "   "}).status_code == 422


def test_search_with_too_long_company_is_422(client):
    assert client.get("/api/leads/search", params={"company": "x" * 101}).status_code == 422


def test_search_route_does_not_shadow_get_by_id(client, lead_payload):
    created = client.post("/api/leads", json=lead_payload).json()
    assert client.get(f"/api/leads/{created['id']}").json() == created
    assert client.get("/api/leads/999").status_code == 404
