# pytest lash/plugins/rec/tests/test_rec.py
import pytest


class TestRecCommand:
    @pytest.mark.skip(
        reason="infinite loop waiting for F3 keypress — not testable without hardware/display"
    )
    def test_rec_skipped(self):
        pass
