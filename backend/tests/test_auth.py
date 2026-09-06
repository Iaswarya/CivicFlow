def test_register_and_login(client):
    r = client.post("/api/auth/register", json={
        "full_name": "Alice", "email": "alice@test.com", "password": "SecurePass1", "role": "INSPECTOR",
    })
    assert r.status_code == 201
    assert r.json()["user"]["email"] == "alice@test.com"

    r2 = client.post("/api/auth/login", json={"email": "alice@test.com", "password": "SecurePass1"})
    assert r2.status_code == 200
    assert "access_token" in r2.json()


def test_login_wrong_password_fails(client):
    client.post("/api/auth/register", json={
        "full_name": "Bob", "email": "bob@test.com", "password": "SecurePass1", "role": "INSPECTOR",
    })
    r = client.post("/api/auth/login", json={"email": "bob@test.com", "password": "wrong"})
    assert r.status_code == 401


def test_duplicate_registration_rejected(client):
    payload = {"full_name": "Carl", "email": "carl@test.com", "password": "SecurePass1", "role": "INSPECTOR"}
    client.post("/api/auth/register", json=payload)
    r = client.post("/api/auth/register", json=payload)
    assert r.status_code == 400


def test_me_requires_token(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401
