from src.utils.color_mapping import frequency_to_rgb


def test_rgb_low_freq():
    assert frequency_to_rgb(80) is not None


def test_rgb_high_freq():
    assert frequency_to_rgb(2000) is not None


def test_rgb_out_of_range():
    assert frequency_to_rgb(50) == (0, 0, 0)
