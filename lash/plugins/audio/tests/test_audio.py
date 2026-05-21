class TestGetLast:
    def test_backslash_path(self):
        from lash.plugins.audio.core import get_last
        assert get_last("C:\\folder\\file.mp4") == "file.mp4"

    def test_forward_slash_path(self):
        from lash.plugins.audio.core import get_last
        assert get_last("/home/user/file.mp3") == "file.mp3"

    def test_path_with_quotes(self):
        from lash.plugins.audio.core import get_last
        assert get_last('/folder/"file.mp4"') == "file.mp4"

    def test_simple_filename(self):
        from lash.plugins.audio.core import get_last
        assert get_last("file.mp4") == "file.mp4"


class TestTupleToSeconds:
    def test_zeros(self):
        from lash.plugins.audio.core import tuple_to_seconds
        assert tuple_to_seconds((0, 0, 0)) == 0

    def test_hours(self):
        from lash.plugins.audio.core import tuple_to_seconds
        assert tuple_to_seconds((1, 0, 0)) == 3600

    def test_minutes(self):
        from lash.plugins.audio.core import tuple_to_seconds
        assert tuple_to_seconds((0, 1, 0)) == 60

    def test_seconds(self):
        from lash.plugins.audio.core import tuple_to_seconds
        assert tuple_to_seconds((0, 0, 1)) == 1

    def test_mixed(self):
        from lash.plugins.audio.core import tuple_to_seconds
        assert tuple_to_seconds((1, 30, 45)) == 5445


def _make_proc(returncode=0):
    from unittest.mock import MagicMock
    proc = MagicMock()
    proc.stdout = iter([])
    proc.returncode = returncode
    return proc


def _make_run(duration_str="Duration: 00:01:00.00"):
    from unittest.mock import MagicMock
    run = MagicMock()
    run.stderr = duration_str
    return run


class TestGetCommand:
    def test_get_without_o(self, tmp_path):
        from unittest.mock import patch
        from click.testing import CliRunner
        from lash.plugins.audio.cli import get

        dummy = tmp_path / "video.mp4"
        dummy.write_bytes(b"fake")

        with patch("subprocess.run", return_value=_make_run()), \
             patch("subprocess.Popen", return_value=_make_proc()) as mock_popen, \
             patch("imageio_ffmpeg.get_ffmpeg_exe", return_value="ffmpeg"):
            CliRunner().invoke(get, [str(dummy)])

        args = mock_popen.call_args[0][0]
        assert args[-1] == str(tmp_path / "video.mp3")

    def test_get_with_o(self, tmp_path):
        from unittest.mock import patch
        from click.testing import CliRunner
        from lash.plugins.audio.cli import get

        dummy = tmp_path / "video.mp4"
        dummy.write_bytes(b"fake")

        with patch("subprocess.run", return_value=_make_run()), \
             patch("subprocess.Popen", return_value=_make_proc()) as mock_popen, \
             patch("imageio_ffmpeg.get_ffmpeg_exe", return_value="ffmpeg"):
            CliRunner().invoke(get, [str(dummy), "-o", "custom"])

        args = mock_popen.call_args[0][0]
        assert args[-1] == str(tmp_path / "custom.mp3")


class TestCutCommand:
    def test_cut_with_both_times(self, tmp_path):
        from unittest.mock import patch
        from click.testing import CliRunner
        from lash.plugins.audio.cli import cut

        dummy = tmp_path / "audio.mp3"
        dummy.write_bytes(b"fake")

        with patch("subprocess.run", return_value=_make_run("Duration: 00:05:00.00")), \
             patch("subprocess.Popen", return_value=_make_proc()) as mock_popen, \
             patch("imageio_ffmpeg.get_ffmpeg_exe", return_value="ffmpeg"):
            CliRunner().invoke(cut, [str(dummy), "-i", "0", "0", "10", "-f", "0", "1", "0"])

        args = mock_popen.call_args[0][0]
        assert "-ss" in args and args[args.index("-ss") + 1] == "10"
        assert "-to" in args and args[args.index("-to") + 1] == "60"

    def test_cut_only_i(self, tmp_path):
        from unittest.mock import patch
        from click.testing import CliRunner
        from lash.plugins.audio.cli import cut

        dummy = tmp_path / "audio.mp3"
        dummy.write_bytes(b"fake")

        with patch("subprocess.run", return_value=_make_run()), \
             patch("subprocess.Popen", return_value=_make_proc()) as mock_popen, \
             patch("imageio_ffmpeg.get_ffmpeg_exe", return_value="ffmpeg"):
            CliRunner().invoke(cut, [str(dummy), "-i", "0", "0", "30"])

        args = mock_popen.call_args[0][0]
        assert "-ss" in args
        assert "-to" not in args

    def test_cut_only_f(self, tmp_path):
        from unittest.mock import patch
        from click.testing import CliRunner
        from lash.plugins.audio.cli import cut

        dummy = tmp_path / "audio.mp3"
        dummy.write_bytes(b"fake")

        with patch("subprocess.run", return_value=_make_run()), \
             patch("subprocess.Popen", return_value=_make_proc()) as mock_popen, \
             patch("imageio_ffmpeg.get_ffmpeg_exe", return_value="ffmpeg"):
            CliRunner().invoke(cut, [str(dummy), "-f", "0", "0", "30"])

        args = mock_popen.call_args[0][0]
        assert "-to" in args
        assert "-ss" not in args

    def test_cut_default_output_name(self, tmp_path):
        from unittest.mock import patch
        from click.testing import CliRunner
        from lash.plugins.audio.cli import cut

        dummy = tmp_path / "audio.mp3"
        dummy.write_bytes(b"fake")

        with patch("subprocess.run", return_value=_make_run()), \
             patch("subprocess.Popen", return_value=_make_proc()) as mock_popen, \
             patch("imageio_ffmpeg.get_ffmpeg_exe", return_value="ffmpeg"):
            CliRunner().invoke(cut, [str(dummy), "-f", "0", "0", "30"])

        args = mock_popen.call_args[0][0]
        assert args[-1] == str(tmp_path / "audio_cutted.mp3")

    def test_cut_s_flag_keeps_original_name(self, tmp_path):
        from unittest.mock import patch
        from click.testing import CliRunner
        from lash.plugins.audio.cli import cut

        dummy = tmp_path / "audio.mp3"
        dummy.write_bytes(b"fake")

        with patch("subprocess.run", return_value=_make_run()), \
             patch("subprocess.Popen", return_value=_make_proc()) as mock_popen, \
             patch("imageio_ffmpeg.get_ffmpeg_exe", return_value="ffmpeg"):
            CliRunner().invoke(cut, [str(dummy), "-s", "-f", "0", "0", "30"])

        args = mock_popen.call_args[0][0]
        assert args[-1] == str(dummy)
