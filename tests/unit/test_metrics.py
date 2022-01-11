from app.metrics.calc import get_list_avg, get_list_max, get_list_min


class TestMetricsFunctions:
    def test_avg_calc_full(self):
        data = [1.0, 1.0, 2.0, 3.0]
        assert get_list_avg(data) == 1.75

    def test_avg_calc_empty(self):
        data = []
        assert get_list_avg(data) == 0.0

    def test_max_full(self):
        data = [1.0, 4.0, 7.0]
        assert get_list_max(data) == 7.0

    def test_max_empty(self):
        data = []
        assert get_list_max(data) == 0.0

    def test_min_full(self):
        data = [1.0, 4.0, 7.0]
        assert get_list_min(data) == 1.0

    def test_min_empty(self):
        data = []
        assert get_list_min(data) == 0.0
