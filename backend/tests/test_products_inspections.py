def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_create_product(client, inspector_token):
    r = client.post("/api/products", json={"product_name": "Sample Atta", "category": "Food"},
                     headers=auth_header(inspector_token))
    assert r.status_code == 201
    assert r.json()["product_name"] == "Sample Atta"


def test_create_inspection(client, inspector_token):
    r = client.post("/api/inspections", json={"notes": "Routine check"}, headers=auth_header(inspector_token))
    assert r.status_code == 201
    assert r.json()["status"] == "NEEDS_MANUAL_REVIEW"


def test_inspection_requires_auth(client):
    r = client.post("/api/inspections", json={})
    assert r.status_code == 401
