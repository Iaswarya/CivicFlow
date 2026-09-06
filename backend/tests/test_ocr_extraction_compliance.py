import io


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def _make_inspection_with_image(client, token):
    insp = client.post("/api/inspections", json={}, headers=auth_header(token)).json()
    fake_image = io.BytesIO(b"fake-image-bytes")
    files = {"file": ("label.jpg", fake_image, "image/jpeg")}
    client.post(f"/api/inspections/{insp['id']}/images", files=files,
                data={"image_type": "front_label"}, headers=auth_header(token))
    return insp["id"]


def test_ocr_demo_mode_runs(client, inspector_token):
    inspection_id = _make_inspection_with_image(client, inspector_token)
    r = client.post(f"/api/ocr/{inspection_id}", headers=auth_header(inspector_token))
    assert r.status_code == 201
    results = r.json()
    assert len(results) == 1
    assert results[0]["is_demo_mode"] is True
    assert "Net Quantity" in results[0]["raw_text"]


def test_extraction_after_ocr(client, inspector_token):
    inspection_id = _make_inspection_with_image(client, inspector_token)
    client.post(f"/api/ocr/{inspection_id}", headers=auth_header(inspector_token))
    r = client.post(f"/api/extraction/{inspection_id}", headers=auth_header(inspector_token))
    assert r.status_code == 201
    fields = {f["field_name"]: f["field_value"] for f in r.json()}
    assert fields["net_quantity"] is not None
    assert fields["mrp"] is not None


def test_extraction_without_ocr_fails(client, inspector_token):
    insp = client.post("/api/inspections", json={}, headers=auth_header(inspector_token)).json()
    r = client.post(f"/api/extraction/{insp['id']}", headers=auth_header(inspector_token))
    assert r.status_code == 400


def test_compliance_with_no_rules_returns_manual_review(client, inspector_token):
    inspection_id = _make_inspection_with_image(client, inspector_token)
    client.post(f"/api/ocr/{inspection_id}", headers=auth_header(inspector_token))
    client.post(f"/api/extraction/{inspection_id}", headers=auth_header(inspector_token))
    r = client.post(f"/api/compliance/{inspection_id}", headers=auth_header(inspector_token))
    assert r.status_code == 200
    # No rules seeded in the test DB -> engine must defer to manual review, never fabricate a pass.
    assert r.json()["overall_result"] == "NEEDS_MANUAL_REVIEW"
