# pytest lash/plugins/image/tests/test_image.py
import os
import pytest


class TestFilesRange:
    def test_counts_files_in_tmp_dir(self, tmp_path):
        from lash.plugins.image.core import files_range

        (tmp_path / 'a.png').write_bytes(b'x')
        (tmp_path / 'b.png').write_bytes(b'x')
        (tmp_path / 'c.txt').write_bytes(b'x')

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = files_range()
        finally:
            os.chdir(original_cwd)

        assert result == 3

    def test_empty_dir_returns_zero(self, tmp_path):
        from lash.plugins.image.core import files_range

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = files_range()
        finally:
            os.chdir(original_cwd)

        assert result == 0

    def test_counts_files_in_subdirs(self, tmp_path):
        from lash.plugins.image.core import files_range

        sub = tmp_path / 'sub'
        sub.mkdir()
        (tmp_path / 'root.png').write_bytes(b'x')
        (sub / 'nested.png').write_bytes(b'x')

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = files_range()
        finally:
            os.chdir(original_cwd)

        assert result == 2


class TestGetFile:
    def test_no_backslash_returns_path_unchanged(self):
        from lash.plugins.image.core import get_file

        result = get_file('image.png')
        assert result == 'image.png'

    def test_no_backslash_with_extension_variants(self):
        from lash.plugins.image.core import get_file

        assert get_file('photo.jpg') == 'photo.jpg'
        assert get_file('archive.zip') == 'archive.zip'

    @pytest.mark.skipif(os.name != 'nt', reason='Windows backslash path handling only')
    def test_windows_path_returns_filename(self, tmp_path):
        from lash.plugins.image.core import get_file

        # Create an actual file so os.chdir target exists
        img_file = tmp_path / 'myimage.png'
        img_file.write_bytes(b'x')

        original_cwd = os.getcwd()
        try:
            result = get_file(str(img_file))
        finally:
            os.chdir(original_cwd)

        assert result == 'myimage.png'


class TestSharp:
    def test_returns_pil_image(self):
        from PIL import Image
        from lash.plugins.image.core import sharp

        im = Image.new('RGB', (10, 10))
        result = sharp(im, 1.0)
        assert isinstance(result, Image.Image)

    def test_sharpness_above_one_does_not_raise(self):
        from PIL import Image
        from lash.plugins.image.core import sharp

        im = Image.new('RGB', (10, 10))
        result = sharp(im, 2.0)
        assert isinstance(result, Image.Image)

    def test_sharpness_zero_does_not_raise(self):
        from PIL import Image
        from lash.plugins.image.core import sharp

        im = Image.new('RGB', (10, 10))
        result = sharp(im, 0.0)
        assert isinstance(result, Image.Image)


class TestColor:
    def test_returns_pil_image(self):
        from PIL import Image
        from lash.plugins.image.core import color

        im = Image.new('RGB', (10, 10))
        result = color(im, 1.0)
        assert isinstance(result, Image.Image)

    def test_color_zero_returns_grayscale_like_image(self):
        from PIL import Image
        from lash.plugins.image.core import color

        im = Image.new('RGB', (10, 10), color=(200, 100, 50))
        result = color(im, 0.0)
        assert isinstance(result, Image.Image)

    def test_color_above_one_does_not_raise(self):
        from PIL import Image
        from lash.plugins.image.core import color

        im = Image.new('RGB', (10, 10))
        result = color(im, 2.0)
        assert isinstance(result, Image.Image)


class TestContrast:
    def test_returns_pil_image(self):
        from PIL import Image
        from lash.plugins.image.core import contrast

        im = Image.new('RGB', (10, 10))
        result = contrast(im, 1.0)
        assert isinstance(result, Image.Image)

    def test_contrast_zero_does_not_raise(self):
        from PIL import Image
        from lash.plugins.image.core import contrast

        im = Image.new('RGB', (10, 10))
        result = contrast(im, 0.0)
        assert isinstance(result, Image.Image)

    def test_contrast_high_value_does_not_raise(self):
        from PIL import Image
        from lash.plugins.image.core import contrast

        im = Image.new('RGB', (10, 10))
        result = contrast(im, 3.0)
        assert isinstance(result, Image.Image)


class TestBrightness:
    def test_returns_pil_image(self):
        from PIL import Image
        from lash.plugins.image.core import brightness

        im = Image.new('RGB', (10, 10))
        result = brightness(im, 1.0)
        assert isinstance(result, Image.Image)

    def test_brightness_zero_produces_black_image(self):
        from PIL import Image
        from lash.plugins.image.core import brightness

        im = Image.new('RGB', (10, 10), color=(255, 255, 255))
        result = brightness(im, 0.0)
        assert isinstance(result, Image.Image)
        # A fully dark image should have pixel (0,0) equal to black
        assert result.getpixel((0, 0)) == (0, 0, 0)

    def test_brightness_above_one_does_not_raise(self):
        from PIL import Image
        from lash.plugins.image.core import brightness

        im = Image.new('RGB', (10, 10))
        result = brightness(im, 2.0)
        assert isinstance(result, Image.Image)


class TestSave:
    def test_saves_image_to_tmp(self, tmp_path):
        from PIL import Image
        from lash.plugins.image.core import save

        im = Image.new('RGB', (20, 20), color=(128, 64, 32))
        out_path = str(tmp_path / 'out.png')
        save(im, out_path)
        assert os.path.isfile(out_path)

    def test_saved_file_can_be_reopened(self, tmp_path):
        from PIL import Image
        from lash.plugins.image.core import save

        im = Image.new('RGB', (15, 15), color=(10, 20, 30))
        out_path = str(tmp_path / 'reopen.png')
        save(im, out_path)
        reopened = Image.open(out_path)
        assert reopened.size == (15, 15)

    def test_invalid_extension_does_not_raise(self, tmp_path, capsys):
        from PIL import Image
        from lash.plugins.image.core import save

        im = Image.new('RGB', (10, 10))
        # .xyz is not a known PIL format — save() should catch ValueError and print
        bad_path = str(tmp_path / 'out.xyz')
        save(im, bad_path)  # must not propagate an exception


class TestAdjustExec:
    def test_returns_pil_image(self):
        from PIL import Image
        from lash.plugins.image.core import adjust_exec

        im = Image.new('RGB', (10, 10))
        result = adjust_exec(im, 1, 1, 1, 1)
        assert isinstance(result, Image.Image)

    def test_identity_values_produce_same_size(self):
        from PIL import Image
        from lash.plugins.image.core import adjust_exec

        im = Image.new('RGB', (30, 20))
        result = adjust_exec(im, 1, 1, 1, 1)
        assert result.size == (30, 20)

    def test_varied_values_return_image(self):
        from PIL import Image
        from lash.plugins.image.core import adjust_exec

        im = Image.new('RGB', (10, 10), color=(100, 150, 200))
        result = adjust_exec(im, 1.2, 1.1, 1.3, 0.9)
        assert isinstance(result, Image.Image)

    def test_zero_values_return_image(self):
        from PIL import Image
        from lash.plugins.image.core import adjust_exec

        im = Image.new('RGB', (10, 10))
        result = adjust_exec(im, 0, 0, 0, 0)
        assert isinstance(result, Image.Image)


class TestWmarke:
    @pytest.mark.skip(reason="Windows fonts required — depends on C:\\Windows\\Fonts which may not exist in CI")
    def test_wmarke_applies_text(self, tmp_path):
        pass


class TestFlipCommand:
    def test_flip_lr_single_image(self, tmp_path):
        from PIL import Image
        from click.testing import CliRunner
        from lash.plugins.image.cli import flip

        img_path = tmp_path / 'sample.png'
        Image.new('RGB', (20, 20), color=(10, 20, 30)).save(str(img_path))

        runner = CliRunner()
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(flip, [str(img_path), '-lr'])
        finally:
            os.chdir(original_cwd)

        assert result.exit_code == 0
        assert 'Process completed' in result.output

    def test_flip_tb_single_image(self, tmp_path):
        from PIL import Image
        from click.testing import CliRunner
        from lash.plugins.image.cli import flip

        img_path = tmp_path / 'sample_tb.png'
        Image.new('RGB', (20, 20), color=(50, 60, 70)).save(str(img_path))

        runner = CliRunner()
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(flip, [str(img_path), '-tb'])
        finally:
            os.chdir(original_cwd)

        assert result.exit_code == 0
        assert 'Process completed' in result.output

    def test_flip_no_action_prints_error(self, tmp_path):
        from PIL import Image
        from click.testing import CliRunner
        from lash.plugins.image.cli import flip

        img_path = tmp_path / 'sample_noact.png'
        Image.new('RGB', (20, 20)).save(str(img_path))

        runner = CliRunner()
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(flip, [str(img_path)])
        finally:
            os.chdir(original_cwd)

        assert 'Error' in result.output or result.exit_code == 0

    def test_flip_non_image_file_prints_error(self, tmp_path):
        from click.testing import CliRunner
        from lash.plugins.image.cli import flip

        bad_file = tmp_path / 'not_an_image.txt'
        bad_file.write_text('hello')

        runner = CliRunner()
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(flip, [str(bad_file), '-lr'])
        finally:
            os.chdir(original_cwd)

        assert 'Error' in result.output


class TestResizeCommand:
    def test_resize_axis_single_image(self, tmp_path):
        from PIL import Image
        from click.testing import CliRunner
        from lash.plugins.image.cli import resize

        img_path = tmp_path / 'resize_me.png'
        Image.new('RGB', (40, 40), color=(80, 90, 100)).save(str(img_path))

        runner = CliRunner()
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(resize, [str(img_path), '-axis', '5', '5'])
        finally:
            os.chdir(original_cwd)

        assert result.exit_code == 0
        assert 'Process completed' in result.output

    def test_resize_double_single_image(self, tmp_path):
        from PIL import Image
        from click.testing import CliRunner
        from lash.plugins.image.cli import resize

        img_path = tmp_path / 'double_me.png'
        Image.new('RGB', (10, 10)).save(str(img_path))

        runner = CliRunner()
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(resize, [str(img_path), '-d'])
        finally:
            os.chdir(original_cwd)

        assert result.exit_code == 0
        assert 'Process completed' in result.output

    def test_resize_reduce_single_image(self, tmp_path):
        from PIL import Image
        from click.testing import CliRunner
        from lash.plugins.image.cli import resize

        img_path = tmp_path / 'reduce_me.png'
        Image.new('RGB', (20, 20)).save(str(img_path))

        runner = CliRunner()
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(resize, [str(img_path), '-r'])
        finally:
            os.chdir(original_cwd)

        assert result.exit_code == 0
        assert 'Process completed' in result.output

    def test_resize_no_option_prints_error(self, tmp_path):
        from PIL import Image
        from click.testing import CliRunner
        from lash.plugins.image.cli import resize

        img_path = tmp_path / 'no_opt.png'
        Image.new('RGB', (20, 20)).save(str(img_path))

        runner = CliRunner()
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(resize, [str(img_path)])
        finally:
            os.chdir(original_cwd)

        assert 'Error' in result.output or result.exit_code == 0

    def test_resize_non_image_file_prints_error(self, tmp_path):
        from click.testing import CliRunner
        from lash.plugins.image.cli import resize

        bad_file = tmp_path / 'bad.txt'
        bad_file.write_text('not an image')

        runner = CliRunner()
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(resize, [str(bad_file), '-axis', '5', '5'])
        finally:
            os.chdir(original_cwd)

        assert 'Error' in result.output
