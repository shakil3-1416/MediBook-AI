from app.main import app


def test_staff_mutation_routes_registered():
    schema = app.openapi()

    collection = (
        "/api/v1/hospital-operations/"
        "{hospital_slug}/staff"
    )

    member = (
        "/api/v1/hospital-operations/"
        "{hospital_slug}/staff/"
        "{membership_id}"
    )

    assert collection in schema["paths"]
    assert member in schema["paths"]

    collection_methods = schema["paths"][collection]
    member_methods = schema["paths"][member]

    assert "get" in collection_methods
    assert "post" in collection_methods
    assert "patch" in member_methods


def test_staff_mutation_contract_shapes():
    schema = app.openapi()

    collection = (
        "/api/v1/hospital-operations/"
        "{hospital_slug}/staff"
    )

    member = (
        "/api/v1/hospital-operations/"
        "{hospital_slug}/staff/"
        "{membership_id}"
    )

    post_operation = schema["paths"][
        collection
    ]["post"]

    patch_operation = schema["paths"][
        member
    ]["patch"]

    assert "requestBody" in post_operation
    assert "requestBody" in patch_operation

    assert "responses" in post_operation
    assert "responses" in patch_operation
