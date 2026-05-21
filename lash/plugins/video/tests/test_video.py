# pytest lash/plugins/video/tests/test_video.py
import pytest


class TestGetLast:
    def test_windows_path_returns_filename(self):
        from lash.plugins.video.core import get_last
        assert get_last("C:\\Users\\kevin\\clips\\video.mp4") == "video.mp4"

    def test_unix_path_returns_filename(self):
        from lash.plugins.video.core import get_last
        assert get_last("/home/user/clips/video.mp4") == "video.mp4"

    def test_simple_filename_no_separator(self):
        from lash.plugins.video.core import get_last
        assert get_last("video.mp4") == "video.mp4"

    def test_strips_surrounding_quotes(self):
        from lash.plugins.video.core import get_last
        assert get_last('/home/user/"my video.mp4"') == "my video.mp4"

    def test_windows_path_with_quotes(self):
        from lash.plugins.video.core import get_last
        assert get_last('C:\\folder\\"clip.avi"') == "clip.avi"

    def test_nested_directory_returns_last_segment(self):
        from lash.plugins.video.core import get_last
        assert get_last("C:\\a\\b\\c\\file.avi") == "file.avi"

    def test_unix_path_single_level(self):
        from lash.plugins.video.core import get_last
        assert get_last("/videos/rec.avi") == "rec.avi"


class TestGetExt:
    def test_returns_extension_lowercase_from_filename(self):
        from lash.plugins.video.core import get_ext
        assert get_ext(file="video.MP4") == ".mp4"

    def test_returns_extension_already_lowercase(self):
        from lash.plugins.video.core import get_ext
        assert get_ext(file="clip.avi") == ".avi"

    def test_returns_extension_from_mkv(self):
        from lash.plugins.video.core import get_ext
        assert get_ext(file="recording.mkv") == ".mkv"

    def test_path_arg_returns_segment_after_last_backslash(self):
        from lash.plugins.video.core import get_ext
        result = get_ext(path="C:\\Users\\kevin\\video.mp4")
        assert result == "video.mp4"

    def test_path_arg_nested_returns_leaf(self):
        from lash.plugins.video.core import get_ext
        result = get_ext(path="C:\\a\\b\\c\\file.avi")
        assert result == "file.avi"

    def test_file_extension_with_multiple_dots(self):
        from lash.plugins.video.core import get_ext
        assert get_ext(file="my.video.clip.mp4") == ".mp4"


class TestPathNoFile:
    def test_removes_filename_from_windows_path(self):
        from lash.plugins.video.core import path_no_file
        result = path_no_file("C:\\Users\\kevin\\video.mp4")
        assert result == "C:\\Users\\kevin\\"

    def test_removes_filename_from_unix_path(self):
        from lash.plugins.video.core import path_no_file
        result = path_no_file("/home/user/clips/video.mp4")
        assert result == "/home/user/clips/"

    def test_filename_only_returns_empty_string(self):
        from lash.plugins.video.core import path_no_file
        result = path_no_file("video.mp4")
        assert result == ""

    def test_nested_windows_path(self):
        from lash.plugins.video.core import path_no_file
        result = path_no_file("C:\\a\\b\\clip.avi")
        assert result == "C:\\a\\b\\"


class TestTupleToSeconds:
    def test_all_zeros_returns_zero(self):
        from lash.plugins.video.core import tuple_to_seconds
        assert tuple_to_seconds((0, 0, 0)) == 0

    def test_hours_converted_correctly(self):
        from lash.plugins.video.core import tuple_to_seconds
        assert tuple_to_seconds((1, 0, 0)) == 3600

    def test_minutes_converted_correctly(self):
        from lash.plugins.video.core import tuple_to_seconds
        assert tuple_to_seconds((0, 1, 0)) == 60

    def test_seconds_only(self):
        from lash.plugins.video.core import tuple_to_seconds
        assert tuple_to_seconds((0, 0, 45)) == 45

    def test_mixed_values(self):
        from lash.plugins.video.core import tuple_to_seconds
        assert tuple_to_seconds((1, 30, 45)) == 5445

    def test_large_values(self):
        from lash.plugins.video.core import tuple_to_seconds
        assert tuple_to_seconds((10, 59, 59)) == 39599

    def test_returns_integer_for_integer_input(self):
        from lash.plugins.video.core import tuple_to_seconds
        result = tuple_to_seconds((0, 2, 30))
        assert result == 150
        assert isinstance(result, int)


def _make_proc(returncode=0):
    from unittest.mock import MagicMock
    proc = MagicMock()
    proc.stdout = iter([])
    proc.returncode = returncode
    return proc


def _make_run(duration_str='Duration: 00:01:00.00'):
    from unittest.mock import MagicMock
    run = MagicMock()
    run.stderr = duration_str
    return run


class TestResumeCommand:
    def test_resume_calls_write_videofile_with_correct_path(self, tmp_path):
        from unittest.mock import patch, MagicMock
        from click.testing import CliRunner
        from lash.plugins.video.cli import resume

        dummy = tmp_path / "my clip.mp4"
        dummy.write_bytes(b"")

        mock_clip = MagicMock()
        mock_clip.duration = 130.0
        mock_clip.subclipped.return_value = MagicMock()
        mock_clip.without_audio.return_value = mock_clip
        mock_concat = MagicMock()

        with patch("lash.plugins.video.cli.VideoFileClip", return_value=mock_clip), \
             patch("lash.plugins.video.cli.concatenate_videoclips", return_value=mock_concat):
            CliRunner().invoke(resume, [str(dummy)])

        expected_path = str(tmp_path / "my_clip-resume.mp4")
        mock_concat.write_videofile.assert_called_once_with(expected_path, logger=None)

    def test_resume_uses_without_audio(self, tmp_path):
        from unittest.mock import patch, MagicMock
        from click.testing import CliRunner
        from lash.plugins.video.cli import resume

        dummy = tmp_path / "demo.mp4"
        dummy.write_bytes(b"")

        mock_clip = MagicMock()
        mock_clip.duration = 26.0
        mock_clip.without_audio.return_value = mock_clip
        mock_clip.subclipped.return_value = MagicMock()
        mock_concat = MagicMock()

        with patch("lash.plugins.video.cli.VideoFileClip", return_value=mock_clip), \
             patch("lash.plugins.video.cli.concatenate_videoclips", return_value=mock_concat):
            CliRunner().invoke(resume, [str(dummy)])

        mock_clip.without_audio.assert_called_once()

    def test_resume_subclipped_called_twelve_times(self, tmp_path):
        from unittest.mock import patch, MagicMock
        from click.testing import CliRunner
        from lash.plugins.video.cli import resume

        dummy = tmp_path / "video.mp4"
        dummy.write_bytes(b"")

        mock_clip = MagicMock()
        mock_clip.duration = 120.0
        mock_clip.without_audio.return_value = mock_clip
        mock_clip.subclipped.return_value = MagicMock()
        mock_concat = MagicMock()

        with patch("lash.plugins.video.cli.VideoFileClip", return_value=mock_clip), \
             patch("lash.plugins.video.cli.concatenate_videoclips", return_value=mock_concat):
            CliRunner().invoke(resume, [str(dummy)])

        assert mock_clip.subclipped.call_count == 12

    def test_resume_concatenate_called_with_compose_method(self, tmp_path):
        from unittest.mock import patch, MagicMock
        from click.testing import CliRunner
        from lash.plugins.video.cli import resume

        dummy = tmp_path / "video.mp4"
        dummy.write_bytes(b"")

        mock_clip = MagicMock()
        mock_clip.duration = 60.0
        mock_clip.without_audio.return_value = mock_clip
        mock_clip.subclipped.return_value = MagicMock()
        mock_concat = MagicMock()

        with patch("lash.plugins.video.cli.VideoFileClip", return_value=mock_clip), \
             patch("lash.plugins.video.cli.concatenate_videoclips", return_value=mock_concat) as mock_cc:
            CliRunner().invoke(resume, [str(dummy)])

        _, kwargs = mock_cc.call_args
        assert kwargs.get("method") == "compose"


class TestCutCommand:
    def test_cut_with_both_times(self, tmp_path):
        from unittest.mock import patch
        from click.testing import CliRunner
        from lash.plugins.video.cli import cut

        dummy = tmp_path / "clip.mp4"
        dummy.write_bytes(b"fake")

        with patch("subprocess.run", return_value=_make_run()), \
             patch("subprocess.Popen", return_value=_make_proc()) as mock_popen, \
             patch("imageio_ffmpeg.get_ffmpeg_exe", return_value="ffmpeg"):
            CliRunner().invoke(cut, [str(dummy), "-i", "0", "0", "10", "-f", "0", "1", "0"])

        args = mock_popen.call_args[0][0]
        assert "-ss" in args and args[args.index("-ss") + 1] == "10"
        assert "-to" in args and args[args.index("-to") + 1] == "60"

    def test_cut_only_i(self, tmp_path):
        from unittest.mock import patch
        from click.testing import CliRunner
        from lash.plugins.video.cli import cut

        dummy = tmp_path / "clip.mp4"
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
        from lash.plugins.video.cli import cut

        dummy = tmp_path / "clip.mp4"
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
        from lash.plugins.video.cli import cut

        dummy = tmp_path / "clip.mp4"
        dummy.write_bytes(b"fake")

        with patch("subprocess.run", return_value=_make_run()), \
             patch("subprocess.Popen", return_value=_make_proc()) as mock_popen, \
             patch("imageio_ffmpeg.get_ffmpeg_exe", return_value="ffmpeg"):
            CliRunner().invoke(cut, [str(dummy), "-f", "0", "0", "30"])

        args = mock_popen.call_args[0][0]
        assert args[-1] == str(tmp_path / "clip_cutted.mp4")

    def test_cut_s_flag_keeps_original_name(self, tmp_path):
        from unittest.mock import patch
        from click.testing import CliRunner
        from lash.plugins.video.cli import cut

        dummy = tmp_path / "clip.mp4"
        dummy.write_bytes(b"fake")

        with patch("subprocess.run", return_value=_make_run()), \
             patch("subprocess.Popen", return_value=_make_proc()) as mock_popen, \
             patch("imageio_ffmpeg.get_ffmpeg_exe", return_value="ffmpeg"):
            CliRunner().invoke(cut, [str(dummy), "-s", "-f", "0", "0", "30"])

        args = mock_popen.call_args[0][0]
        assert args[-1] == str(dummy)


class TestIntroCommand:
    def test_intro_default_output(self, tmp_path):
        from unittest.mock import patch
        from click.testing import CliRunner
        from lash.plugins.video.cli import intro

        video_file = tmp_path / "main.mp4"
        intro_file = tmp_path / "intro.mp4"
        video_file.write_bytes(b"fake")
        intro_file.write_bytes(b"fake")

        with patch("subprocess.run", return_value=_make_run()), \
             patch("subprocess.Popen", return_value=_make_proc()) as mock_popen, \
             patch("imageio_ffmpeg.get_ffmpeg_exe", return_value="ffmpeg"):
            CliRunner().invoke(intro, [str(video_file), str(intro_file)])

        args = mock_popen.call_args[0][0]
        assert args[-1] == str(tmp_path / "main_with_intro.mp4")

    def test_intro_s_flag_overwrites_original(self, tmp_path):
        from unittest.mock import patch
        from click.testing import CliRunner
        from lash.plugins.video.cli import intro

        video_file = tmp_path / "main.mp4"
        intro_file = tmp_path / "intro.mp4"
        video_file.write_bytes(b"fake")
        intro_file.write_bytes(b"fake")

        with patch("subprocess.run", return_value=_make_run()), \
             patch("subprocess.Popen", return_value=_make_proc()) as mock_popen, \
             patch("imageio_ffmpeg.get_ffmpeg_exe", return_value="ffmpeg"):
            CliRunner().invoke(intro, [str(video_file), str(intro_file), "-s"])

        args = mock_popen.call_args[0][0]
        assert args[-1] == str(video_file)


class TestEndCommand:
    def test_end_default_output(self, tmp_path):
        from unittest.mock import patch
        from click.testing import CliRunner
        from lash.plugins.video.cli import end

        video_file = tmp_path / "main.mp4"
        end_file = tmp_path / "credits.mp4"
        video_file.write_bytes(b"fake")
        end_file.write_bytes(b"fake")

        with patch("subprocess.run", return_value=_make_run()), \
             patch("subprocess.Popen", return_value=_make_proc()) as mock_popen, \
             patch("imageio_ffmpeg.get_ffmpeg_exe", return_value="ffmpeg"):
            CliRunner().invoke(end, [str(video_file), str(end_file)])

        args = mock_popen.call_args[0][0]
        assert args[-1] == str(tmp_path / "main_with_end.mp4")

    def test_end_s_flag_overwrites_original(self, tmp_path):
        from unittest.mock import patch
        from click.testing import CliRunner
        from lash.plugins.video.cli import end

        video_file = tmp_path / "main.mp4"
        end_file = tmp_path / "credits.mp4"
        video_file.write_bytes(b"fake")
        end_file.write_bytes(b"fake")

        with patch("subprocess.run", return_value=_make_run()), \
             patch("subprocess.Popen", return_value=_make_proc()) as mock_popen, \
             patch("imageio_ffmpeg.get_ffmpeg_exe", return_value="ffmpeg"):
            CliRunner().invoke(end, [str(video_file), str(end_file), "-s"])

        args = mock_popen.call_args[0][0]
        assert args[-1] == str(video_file)


class TestBuildCommand:
    @pytest.mark.skip(reason="requires real filesystem with jpeg images, cv2 VideoWriter, and os.chdir side-effects")
    def test_build_skipped(self):
        pass


class TestRecCommand:
    @pytest.mark.skip(reason="infinite loop waiting for F3 keypress — not testable without hardware/display")
    def test_rec_skipped(self):
        pass
