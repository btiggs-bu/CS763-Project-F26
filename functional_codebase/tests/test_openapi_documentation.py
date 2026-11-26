from app.main import app


def _has_example(value: dict) -> bool:
    return "example" in value or bool(value.get("examples"))


def test_api_operations_have_complete_openapi_documentation() -> None:
    specification = app.openapi()
    methods = {"get", "post", "patch", "put", "delete"}
    operations = [
        (path, method, operation)
        for path, path_item in specification["paths"].items()
        for method, operation in path_item.items()
        if method in methods
    ]

    assert operations
    for path, method, operation in operations:
        assert operation.get("summary"), f"{method.upper()} {path} lacks summary"
        assert operation.get("description"), (
            f"{method.upper()} {path} lacks description"
        )

        for status_code, response in operation["responses"].items():
            assert response.get("description"), (
                f"{method.upper()} {path} response {status_code} lacks description"
            )
            if status_code == "204":
                assert "content" not in response
                continue
            if status_code.startswith("2") and response.get("content"):
                for media_type, media in response["content"].items():
                    assert media.get("schema"), (
                        f"{method.upper()} {path} response {status_code} "
                        f"({media_type}) lacks a schema"
                    )
                    assert _has_example(media), (
                        f"{method.upper()} {path} response {status_code} "
                        f"({media_type}) lacks an example"
                    )

        request_body = operation.get("requestBody")
        if request_body:
            for media_type, media in request_body["content"].items():
                assert _has_example(media), (
                    f"{method.upper()} {path} request ({media_type}) lacks an example"
                )

        for parameter in operation.get("parameters", []):
            parameter_schema = parameter.get("schema", {})
            has_parameter_example = (
                "example" in parameter
                or bool(parameter.get("examples"))
                or "example" in parameter_schema
                or bool(parameter_schema.get("examples"))
            )
            assert has_parameter_example, (
                f"{method.upper()} {path} parameter {parameter['name']} "
                "lacks an example"
            )
