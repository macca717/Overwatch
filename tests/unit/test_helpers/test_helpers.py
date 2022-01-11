import os
from time import sleep
import pytest
import pytest_check as check
from app.helpers import retry, get_elapsed_time_s, TimeoutAfter, feature_enabled


class TestRetrys:
    def test_retry_success(self):
        @retry(Exception)
        def passes():
            return 7

        assert passes() == 7

    def test_retry_failure(self):
        @retry(Exception, delay=0)
        def fails():
            raise Exception("Fails")

        with pytest.raises(Exception):
            fails()


class TestTimers:
    @pytest.mark.repeat(10)
    def test_get_elapsed_helper(self):
        def test():
            sleep(0.1)
            return 14

        (elapsed, result) = get_elapsed_time_s(test)
        check.almost_equal(elapsed, 0.10, abs=7e-2)
        check.equal(result, 14)

    @pytest.mark.repeat(10)
    def test_get_elapsed_helper_args(self):
        def test(value):
            sleep(0.1)
            return value

        (elapsed, result) = get_elapsed_time_s(test, 14)
        check.almost_equal(elapsed, 0.10, abs=7e-2)
        check.equal(result, 14)

    def test_timeout_after_exit_early(self):
        with TimeoutAfter(timeout=10):
            sleep(1)

    def test_timeout_after_late(self):
        with pytest.raises(TimeoutError):
            with TimeoutAfter(timeout=3):
                sleep(5)


class TestFeatureFlags:
    def test_feature_enabled(self, monkeypatch):
        flag = "FF_TEST_FEATURE"
        monkeypatch.setenv(flag, "1")
        assert feature_enabled(flag)

    def test_feature_disabled(self):
        flag = "FF_TEST_FEATURE"
        assert not feature_enabled(flag)
