from app.data.generator import generate_dataset


def test_generate_dataset():

    dataset = generate_dataset(
        size=100,
        dimensions=16
    )

    assert len(dataset) == 100

    assert len(dataset[0].vector) == 16