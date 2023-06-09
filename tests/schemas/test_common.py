from pydantic import ValidationError
import pytest

from trytune.schemas.common import InferSchema


def test_infer_schema() -> None:
    valid_data = {
        "target": "pipe1",
        "inputs": {
            "i1": {"data": [1, 2, 3], "shape": [1, 3]},
            "i2": {"data": [4, 5, 6]},
        },
    }

    # Test valid data
    try:
        infer = InferSchema(**valid_data)
    except ValidationError as e:
        assert False, f"Failed to create InferSchema instance with valid data: {e}"

    # Access schema fields
    assert infer.target == "pipe1"
    assert "i1" in infer.inputs
    assert infer.inputs["i1"].data == [1, 2, 3]
    assert infer.inputs["i1"].shape is not None
    assert infer.inputs["i1"].shape == [1, 3]
    assert "i2" in infer.inputs
    assert infer.inputs["i2"].data == [4, 5, 6]
    assert infer.inputs["i2"].shape is None

    invalid_data = {
        "target": "pipe1",
    }

    with pytest.raises(ValidationError):
        InferSchema(**invalid_data)
