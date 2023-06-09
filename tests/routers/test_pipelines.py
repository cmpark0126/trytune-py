from PIL import Image
import cv2
import numpy as np
import torchvision.transforms as T


def test_pipelines_scenario(client) -> None:  # type: ignore
    detection_module = "detection_module"
    add_module_schema = {
        "name": detection_module,
        "type": "builtin",
        "builtin_args": {"target": "FasterRCNN_ResNet50_FPN"},
    }

    response = client.post("/modules/add", json=add_module_schema)
    assert response.status_code == 200, response.content
    # detection_module_metadata = response.json()
    # print(detection_module_metadata)

    crop_module = "crop_module"
    add_module_schema = {
        "name": crop_module,
        "type": "builtin",
        "builtin_args": {
            "target": "Crop",
            "threshold": 0.9,
            "label": 1,  # label 1 is person
        },
    }

    response = client.post("/modules/add", json=add_module_schema)
    assert response.status_code == 200, response.content
    # crop_module_metadata = response.json()
    # print(crop_module_metadata)

    pipeline = "test_pipeline"
    add_pipeline_schema = {
        "name": pipeline,
        "tensors": {
            "inputs": [{"name": "p_image"}],
            "outputs": [{"name": "p_cropped_images"}, {"name": "p_whs"}],
        },
        "stages": [
            {
                "name": "detector",
                "module": "detection_module",
                "inputs": {"BATCH_IMAGE": {"name": "p_image"}},
                "outputs": {
                    "BOXES": {"name": "p_boxes"},
                    "LABELS": {"name": "p_labels"},
                    "SCORES": {"name": "p_scores"},
                },
            },
            {
                "name": "cropper",
                "module": "crop_module",
                "inputs": {
                    "IMAGE": {"name": "p_image"},
                    "BOXES": {"name": "p_boxes"},
                    "LABELS": {"name": "p_labels"},
                    "SCORES": {"name": "p_scores"},
                },
                "outputs": {
                    "CROPPED_IMAGES": {"name": "p_cropped_images"},
                    "WHS": {"name": "p_whs"},
                },
            },
        ],
    }

    response = client.post("/pipelines/add", json=add_pipeline_schema)
    assert response.status_code == 200, response.content
    # pipeline_metadata = response.json()

    # Set scheduler
    scheduler_schema = {"name": "fifo", "config": {}}
    response = client.post("/scheduler/set", json=scheduler_schema)
    assert response.status_code == 200, response.content

    # Load input image
    img_pil = Image.open("./assets/FudanPed00054.png").convert("RGB")
    transform = T.Compose([T.ToTensor()])
    img = transform(img_pil)
    batch_img = img.unsqueeze(0)

    infer_schema = {
        "target": add_pipeline_schema["name"],
        "inputs": {
            "p_image": {
                "data": batch_img.numpy().tolist(),
                "shape": batch_img.shape,
            }
        },
    }
    response = client.post(
        f"/pipelines/{add_pipeline_schema['name']}/infer", json=infer_schema
    )
    assert response.status_code == 200, response.content
    result = response.json()

    assert "p_cropped_images" in result
    assert "p_whs" in result
    cropped_images = result["p_cropped_images"]
    whs = result["p_whs"]

    # NOTE: wh can be used to crop padding from cropped image
    print("\n>> Result is cropped at ./assets/FudanPed00054_person_{ ", end="")
    for i, (cropped_image, wh) in enumerate(zip(cropped_images, whs)):
        cropped_np = np.transpose(np.array(cropped_image), (1, 2, 0)).astype(np.float32)
        # cropped_np = cv2.resize(cropped_np, (wh[0], wh[1]))
        cropped_cv = cv2.cvtColor(cropped_np * 255, cv2.COLOR_RGB2BGR)
        cv2.imwrite("./assets/FudanPed00054_person_" + f"{i}" + ".png", cropped_cv)
        print(i, ", ", end="")
    print(".png } << ")


# TODO: add more scenarios for testing (e.g., classification, object detection, etc.)
# For testing on k8s
def test_pipelines_scenario_on_k8s(client, add_module_schemas, add_pipeline_schema) -> None:  # type: ignore
    pass
