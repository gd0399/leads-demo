def test_index_renders_empty_state(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "No leads" in r.text


def test_form_post_creates_lead_and_redirects(client):
    r = client.post(
        "/leads",
        data={"name": "Ada", "company": "Acme", "region": "EMEA", "status": "won"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/"

    page = client.get("/").text
    assert "Ada" in page and "Acme" in page and "EMEA" in page
    assert 'class="badge won"' in page


def test_form_post_with_blank_name_shows_error_and_keeps_input(client):
    r = client.post("/leads", data={"name": "  ", "company": "Acme", "region": "EMEA"})
    assert r.status_code == 422
    assert 'class="error"' in r.text
    assert 'value="Acme"' in r.text  # the rest of the form is preserved
    assert client.get("/api/leads").json() == []  # nothing was saved


def test_index_filters_by_status(client, lead_payload):
    client.post("/api/leads", json=lead_payload)  # qualified
    client.post("/api/leads", json={**lead_payload, "name": "Bob", "status": "lost"})

    page = client.get("/", params={"status": "lost"}).text
    assert "Bob" in page
    assert "Ada Lovelace" not in page

    page = client.get("/", params={"status": "contacted"}).text
    assert 'No leads with status "contacted"' in page


def test_index_with_invalid_status_is_422(client):
    assert client.get("/", params={"status": "bogus"}).status_code == 422
