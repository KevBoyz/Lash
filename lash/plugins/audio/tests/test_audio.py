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


class TestGetCommand:
    def test_get_without_o(self, tmp_path):
        from unittest.mock import patch, MagicMock
        from click.testing import CliRunner
        from lash.plugins.audio.cli import get

        dummy = tmp_path / "video.mp4"
        dummy.write_bytes(b"")

        mock_clip = MagicMock()
        with patch("lash.plugins.audio.cli.VideoFileClip", return_value=mock_clip):
            runner = CliRunner()
            runner.invoke(get, [str(dummy)])

        expected = str(dummy).replace(".mp4", ".mp3")
        mock_clip.audio.write_audiofile.assert_called_once_with(expected)

    def test_get_with_o(self, tmp_path):
        from unittest.mock import patch, MagicMock
        from click.testing import CliRunner
        from lash.plugins.audio.cli import get

        dummy = tmp_path / "video.mp4"
        dummy.write_bytes(b"")

        mock_clip = MagicMock()
        with patch("lash.plugins.audio.cli.VideoFileClip", return_value=mock_clip):
            runner = CliRunner()
            runner.invoke(get, [str(dummy), "-o", "custom"])

        from lash.plugins.audio.core import get_last
        filename = get_last(str(dummy))
        expected = f'{str(dummy).replace(filename, "custom")}.mp3'
        mock_clip.audio.write_audiofile.assert_called_once_with(expected)


class TestCutCommand:
    def test_cut_with_times(self, tmp_path):
        from unittest.mock import patch, MagicMock
        from click.testing import CliRunner
        from lash.plugins.audio.cli import cut

        dummy = tmp_path / "audio.mp3"
        dummy.write_bytes(b"")

        mock_audio = MagicMock()
        with patch("lash.plugins.audio.cli.AudioFileClip", return_value=mock_audio):
            runner = CliRunner()
            runner.invoke(cut, [str(dummy), "-i", "0", "0", "10", "-f", "0", "1", "0"])

        mock_audio.subclip.assert_called_once_with(10, 60)
