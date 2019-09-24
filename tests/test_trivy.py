from ecranner.trivy import trivy


def test_trivy_run():
    # you need to pull image_name
    image_name = 'alpine:latest'
    result = trivy(image_name)
    assert isinstance(result, list) is True


def test_trivy_run_nonexistance_image():
    image_name = 'nonexistant_image'
    result = trivy(image_name)
    assert result is None
