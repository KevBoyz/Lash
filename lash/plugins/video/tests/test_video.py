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
        # when `path` is provided, returns everything after the last backslash
        result = get_ext(path="C:\\Users\\kevin\\video.mp4")
        assert result == "video.mp4"

    def test_path_arg_nested_returns_leaf(self):
        from lash.plugins.video.core import get_ext
        result = get_ext(path="C:\\a\\b\\c\\file.avi")
        assert result == "file.avi"

    def test_file_extension_with_multiple_dots(self):
        from lash.plugins.video.core import get_ext
        # rfind('.') picks the last dot
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
        # get_last returns the whole string; replacing it leaves ''
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


class TestResumeCommand:
    def test_resume_calls_write_videofile_with_correct_path(self, tmp_path):
        from unittest.mock import patch, MagicMock
        from click.testing import CliRunner
        from lash.plugins.video.cli import resume

        dummy = tmp_path / "my clip.mp4"
        dummy.write_bytes(b"")

        mock_clip = MagicMock()
        mock_clip.duration = 130.0
        mock_sub = MagicMock()
        mock_clip.subclip.return_value = mock_sub
        mock_clip.without_audio.return_value = mock_clip

        mock_concat = MagicMock()

        with patch("lash.plugins.video.cli.VideoFileClip", return_value=mock_clip), \
             patch("lash.plugins.video.cli.concatenate_videoclips", return_value=mock_concat):
            runner = CliRunner()
            result = runner.invoke(resume, [str(dummy)])

        expected_name = "my_clip-resume.mp4"
        expected_path = str(tmp_path / expected_name)
        mock_concat.write_videofile.assert_called_once_with(expected_path)

    def test_resume_uses_without_audio(self, tmp_path):
        from unittest.mock import patch, MagicMock
        from click.testing import CliRunner
        from lash.plugins.video.cli import resume

        dummy = tmp_path / "demo.mp4"
        dummy.write_bytes(b"")

        mock_clip = MagicMock()
        mock_clip.duration = 26.0
        mock_clip.without_audio.return_value = mock_clip
        mock_clip.subclip.return_value = MagicMock()
        mock_concat = MagicMock()

        with patch("lash.plugins.video.cli.VideoFileClip", return_value=mock_clip), \
             patch("lash.plugins.video.cli.concatenate_videoclips", return_value=mock_concat):
            runner = CliRunner()
            runner.invoke(resume, [str(dummy)])

        mock_clip.without_audio.assert_called_once()

    def test_resume_subclip_called_twelve_times(self, tmp_path):
        from unittest.mock import patch, MagicMock
        from click.testing import CliRunner
        from lash.plugins.video.cli import resume

        dummy = tmp_path / "video.mp4"
        dummy.write_bytes(b"")

        mock_clip = MagicMock()
        mock_clip.duration = 120.0
        mock_clip.without_audio.return_value = mock_clip
        mock_clip.subclip.return_value = MagicMock()
        mock_concat = MagicMock()

        with patch("lash.plugins.video.cli.VideoFileClip", return_value=mock_clip), \
             patch("lash.plugins.video.cli.concatenate_videoclips", return_value=mock_concat):
            runner = CliRunner()
            runner.invoke(resume, [str(dummy)])

        assert mock_clip.subclip.call_count == 12

    def test_resume_concatenate_called_with_compose_method(self, tmp_path):
        from unittest.mock import patch, MagicMock, call
        from click.testing import CliRunner
        from lash.plugins.video.cli import resume

        dummy = tmp_path / "video.mp4"
        dummy.write_bytes(b"")

        mock_clip = MagicMock()
        mock_clip.duration = 60.0
        mock_clip.without_audio.return_value = mock_clip
        mock_clip.subclip.return_value = MagicMock()
        mock_concat = MagicMock()

        with patch("lash.plugins.video.cli.VideoFileClip", return_value=mock_clip) as mock_vfc, \
             patch("lash.plugins.video.cli.concatenate_videoclips", return_value=mock_concat) as mock_cc:
            runner = CliRunner()
            runner.invoke(resume, [str(dummy)])

        _, kwargs = mock_cc.call_args
        assert kwargs.get("method") == "compose"


class TestCutCommand:
    def test_cut_calls_subclip_with_correct_seconds(self, tmp_path):
        from unittest.mock import patch, MagicMock
        from click.testing import CliRunner
        from lash.plugins.video.cli import cut

        dummy = tmp_path / "clip.mp4"
        dummy.write_bytes(b"")

        mock_video = MagicMock()
        mock_subclip = MagicMock()
        mock_video.subclip.return_value = mock_subclip

        with patch("lash.plugins.video.cli.VideoFileClip", return_value=mock_video):
            runner = CliRunner()
            result = runner.invoke(cut, [
                str(dummy),
                "-i", "0", "0", "10",
                "-f", "0", "1", "0",
            ])

        # initial=10s, final=60s
        mock_video.subclip.assert_called_once_with(10, 60)

    def test_cut_with_hours_minutes_seconds(self, tmp_path):
        from unittest.mock import patch, MagicMock
        from click.testing import CliRunner
        from lash.plugins.video.cli import cut

        dummy = tmp_path / "long.mp4"
        dummy.write_bytes(b"")

        mock_video = MagicMock()
        mock_video.subclip.return_value = MagicMock()

        with patch("lash.plugins.video.cli.VideoFileClip", return_value=mock_video):
            runner = CliRunner()
            runner.invoke(cut, [
                str(dummy),
                "-i", "1", "0", "0",
                "-f", "1", "30", "0",
            ])

        # initial=3600s, final=5400s
        mock_video.subclip.assert_called_once_with(3600, 5400)

    def test_cut_with_o_writes_to_custom_output(self, tmp_path):
        from unittest.mock import patch, MagicMock
        from click.testing import CliRunner
        from lash.plugins.video.cli import cut

        dummy = tmp_path / "video.mp4"
        dummy.write_bytes(b"")

        mock_video = MagicMock()
        mock_subclip = MagicMock()
        mock_video.subclip.return_value = mock_subclip

        with patch("lash.plugins.video.cli.VideoFileClip", return_value=mock_video):
            runner = CliRunner()
            runner.invoke(cut, [
                str(dummy),
                "-o", "output",
                "-i", "0", "0", "0",
                "-f", "0", "0", "30",
            ])

        from lash.plugins.video.core import get_last
        filename = get_last(str(dummy))
        expected = f'{str(dummy).replace(filename, "output")}.mp4'
        mock_subclip.write_videofile.assert_called_once_with(expected)

    def test_cut_without_o_writes_to_original_path(self, tmp_path):
        from unittest.mock import patch, MagicMock
        from click.testing import CliRunner
        from lash.plugins.video.cli import cut

        dummy = tmp_path / "video.mp4"
        dummy.write_bytes(b"")

        mock_video = MagicMock()
        mock_subclip = MagicMock()
        mock_video.subclip.return_value = mock_subclip

        with patch("lash.plugins.video.cli.VideoFileClip", return_value=mock_video):
            runner = CliRunner()
            runner.invoke(cut, [
                str(dummy),
                "-i", "0", "0", "0",
                "-f", "0", "0", "10",
            ])

        mock_subclip.write_videofile.assert_called_once_with(str(dummy))

    def test_cut_zero_to_zero_calls_subclip(self, tmp_path):
        from unittest.mock import patch, MagicMock
        from click.testing import CliRunner
        from lash.plugins.video.cli import cut

        dummy = tmp_path / "video.mp4"
        dummy.write_bytes(b"")

        mock_video = MagicMock()
        mock_video.subclip.return_value = MagicMock()

        with patch("lash.plugins.video.cli.VideoFileClip", return_value=mock_video):
            runner = CliRunner()
            runner.invoke(cut, [
                str(dummy),
                "-i", "0", "0", "0",
                "-f", "0", "0", "0",
            ])

        mock_video.subclip.assert_called_once_with(0, 0)


class TestIntroCommand:
    def test_intro_concatenates_intro_then_video(self, tmp_path):
        from unittest.mock import patch, MagicMock, call
        from click.testing import CliRunner
        from lash.plugins.video.cli import intro

        video_file = tmp_path / "main.mp4"
        intro_file = tmp_path / "intro.mp4"
        video_file.write_bytes(b"")
        intro_file.write_bytes(b"")

        mock_video = MagicMock()
        mock_intro = MagicMock()
        mock_composed = MagicMock()

        def fake_vfc(path):
            if path == str(video_file):
                return mock_video
            return mock_intro

        with patch("lash.plugins.video.cli.VideoFileClip", side_effect=fake_vfc), \
             patch("lash.plugins.video.cli.concatenate_videoclips", return_value=mock_composed) as mock_cc:
            runner = CliRunner()
            runner.invoke(intro, [str(video_file), str(intro_file)])

        args, _ = mock_cc.call_args
        assert args[0] == [mock_intro, mock_video]

    def test_intro_without_o_writes_to_original_path(self, tmp_path):
        from unittest.mock import patch, MagicMock
        from click.testing import CliRunner
        from lash.plugins.video.cli import intro

        video_file = tmp_path / "main.mp4"
        intro_file = tmp_path / "intro.mp4"
        video_file.write_bytes(b"")
        intro_file.write_bytes(b"")

        mock_composed = MagicMock()

        with patch("lash.plugins.video.cli.VideoFileClip", return_value=MagicMock()), \
             patch("lash.plugins.video.cli.concatenate_videoclips", return_value=mock_composed):
            runner = CliRunner()
            runner.invoke(intro, [str(video_file), str(intro_file)])

        mock_composed.write_videofile.assert_called_once_with(str(video_file))

    def test_intro_with_o_writes_to_custom_output(self, tmp_path):
        from unittest.mock import patch, MagicMock
        from click.testing import CliRunner
        from lash.plugins.video.cli import intro

        video_file = tmp_path / "main.mp4"
        intro_file = tmp_path / "intro.mp4"
        video_file.write_bytes(b"")
        intro_file.write_bytes(b"")

        mock_composed = MagicMock()

        with patch("lash.plugins.video.cli.VideoFileClip", return_value=MagicMock()), \
             patch("lash.plugins.video.cli.concatenate_videoclips", return_value=mock_composed):
            runner = CliRunner()
            runner.invoke(intro, [str(video_file), str(intro_file), "-o", "final"])

        from lash.plugins.video.core import get_last
        filename = get_last(str(video_file))
        expected = f'{str(video_file).replace(filename, "final")}.mp4'
        mock_composed.write_videofile.assert_called_once_with(expected)


class TestEndCommand:
    def test_end_concatenates_video_then_end(self, tmp_path):
        from unittest.mock import patch, MagicMock
        from click.testing import CliRunner
        from lash.plugins.video.cli import end

        video_file = tmp_path / "main.mp4"
        end_file = tmp_path / "credits.mp4"
        video_file.write_bytes(b"")
        end_file.write_bytes(b"")

        mock_video = MagicMock()
        mock_end = MagicMock()
        mock_composed = MagicMock()

        def fake_vfc(path):
            if path == str(video_file):
                return mock_video
            return mock_end

        with patch("lash.plugins.video.cli.VideoFileClip", side_effect=fake_vfc), \
             patch("lash.plugins.video.cli.concatenate_videoclips", return_value=mock_composed) as mock_cc:
            runner = CliRunner()
            runner.invoke(end, [str(video_file), str(end_file)])

        args, _ = mock_cc.call_args
        assert args[0] == [mock_video, mock_end]

    def test_end_without_o_writes_to_original_path(self, tmp_path):
        from unittest.mock import patch, MagicMock
        from click.testing import CliRunner
        from lash.plugins.video.cli import end

        video_file = tmp_path / "main.mp4"
        end_file = tmp_path / "credits.mp4"
        video_file.write_bytes(b"")
        end_file.write_bytes(b"")

        mock_composed = MagicMock()

        with patch("lash.plugins.video.cli.VideoFileClip", return_value=MagicMock()), \
             patch("lash.plugins.video.cli.concatenate_videoclips", return_value=mock_composed):
            runner = CliRunner()
            runner.invoke(end, [str(video_file), str(end_file)])

        mock_composed.write_videofile.assert_called_once_with(str(video_file))

    def test_end_with_o_writes_to_custom_output(self, tmp_path):
        from unittest.mock import patch, MagicMock
        from click.testing import CliRunner
        from lash.plugins.video.cli import end

        video_file = tmp_path / "main.mp4"
        end_file = tmp_path / "credits.mp4"
        video_file.write_bytes(b"")
        end_file.write_bytes(b"")

        mock_composed = MagicMock()

        with patch("lash.plugins.video.cli.VideoFileClip", return_value=MagicMock()), \
             patch("lash.plugins.video.cli.concatenate_videoclips", return_value=mock_composed):
            runner = CliRunner()
            runner.invoke(end, [str(video_file), str(end_file), "-o", "with_credits"])

        from lash.plugins.video.core import get_last
        filename = get_last(str(video_file))
        expected = f'{str(video_file).replace(filename, "with_credits")}.mp4'
        mock_composed.write_videofile.assert_called_once_with(expected)


class TestBuildCommand:
    @pytest.mark.skip(reason="requires real filesystem with jpeg images, cv2 VideoWriter, and os.chdir side-effects")
    def test_build_skipped(self):
        pass


class TestRecCommand:
    @pytest.mark.skip(reason="infinite loop waiting for F3 keypress — not testable without hardware/display")
    def test_rec_skipped(self):
        pass
