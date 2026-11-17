# pytest lash/plugins/share/tests/test_page_zip.py
# Runs the page's zip code (static/index.html) in Node and opens the result with zipfile.
import shutil
import pytest

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")

_RUNNER = """
const fs = require('fs');
/*ZIP*/
(async () => {
  const spec = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const files = spec.files.map(([name, text]) => new File([text], name));
  // Like Chrome reading a file that is locked or changed after being picked.
  for (const name of spec.unreadable) {
    files.splice(1, 0, {name, size: 10, lastModified: 0, stream: () => new ReadableStream({
      pull(controller) { controller.error(new TypeError('network error')); },
    })});
  }
  for (let i = 0; i < spec.empty; i++) files.push(new File([], 'docs/e' + i + '.txt'));
  const progress = [];
  const {blob, skipped} = await buildZip(files, (read, total, index) =>
    progress.push([read, total, index]));
  fs.writeFileSync(process.argv[3], Buffer.from(await blob.arrayBuffer()));
  fs.writeFileSync(process.argv[4], JSON.stringify({progress, skipped}));
})().catch((err) => { console.error(err); process.exit(1); });
"""

_FILES = [["docs/a.txt", "hello"], ["docs/sub/ação.txt", "olá"], ["docs/vazio.txt", ""]]


def _zip_code(zip64_from):
    from pathlib import Path
    html = (Path(__file__).parents[1] / "static" / "index.html").read_text(encoding="utf-8")
    code = html[html.index("// ---------- zip"):html.index("// ---------- wiring")]
    if zip64_from is not None:
        limit = "const ZIP64_FROM = 0xFFFFFFFF;"
        assert limit in code
        code = code.replace(limit, f"const ZIP64_FROM = {zip64_from};")
    return code


def _build(tmp_path, files=_FILES, empty=0, unreadable=(), zip64_from=None):
    """Bytes of the zip the page builds for `files` plus `empty` empty files.

    `unreadable` files (10 B each) fail when read. The progress calls [read, total, index]
    and the skipped paths go to tmp_path / "result.json".
    """
    import json
    import subprocess
    script = tmp_path / "zip.js"
    script.write_text(_RUNNER.replace("/*ZIP*/", _zip_code(zip64_from)), encoding="utf-8")
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps({"files": files, "empty": empty, "unreadable": list(unreadable)}),
                    encoding="utf-8")
    out = tmp_path / "out.zip"
    subprocess.run([shutil.which("node"), str(script), str(spec), str(out),
                    str(tmp_path / "result.json")],
                   check=True, capture_output=True, timeout=300)
    return out.read_bytes()


def _result(tmp_path):
    import json
    return json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))


def _assert_conteudo(zf):
    assert zf.testzip() is None
    assert zf.namelist() == [name for name, _ in _FILES]
    for name, text in _FILES:
        assert zf.read(name) == text.encode("utf-8")


class TestZipDaPagina:
    def test_zip_pequeno_fica_no_formato_classico(self, tmp_path):
        import io
        import zipfile
        raw = _build(tmp_path)
        _assert_conteudo(zipfile.ZipFile(io.BytesIO(raw)))
        assert b"PK\x06\x06" not in raw

    def test_acima_do_limite_usa_zip64_e_abre_normalmente(self, tmp_path):
        import io
        import zipfile
        raw = _build(tmp_path, zip64_from=0)
        assert b"PK\x06\x06" in raw and b"PK\x06\x07" in raw
        zf = zipfile.ZipFile(io.BytesIO(raw))
        _assert_conteudo(zf)
        for info in zf.infolist():
            assert info.extra.startswith(b"\x01\x00")
            assert info.file_size == info.compress_size

    def test_progresso_vai_de_zero_ao_total_de_bytes(self, tmp_path):
        _build(tmp_path)
        progress = _result(tmp_path)["progress"]
        total = sum(len(text.encode("utf-8")) for _, text in _FILES)
        assert progress[0] == [0, total, 0]
        assert progress[-1] == [total, total, len(_FILES) - 1]
        reads = [read for read, _, _ in progress]
        assert reads == sorted(reads)

    def test_arquivo_ilegivel_fica_de_fora_e_o_resto_e_zipado(self, tmp_path):
        import io
        import zipfile
        raw = _build(tmp_path, unreadable=["docs/Thumbs.db"])
        _assert_conteudo(zipfile.ZipFile(io.BytesIO(raw)))
        result = _result(tmp_path)
        assert result["skipped"] == ["docs/Thumbs.db"]
        total = sum(len(text.encode("utf-8")) for _, text in _FILES) + 10
        assert result["progress"][-1][:2] == [total, total]

    def test_sem_arquivos_ilegiveis_nada_fica_de_fora(self, tmp_path):
        _build(tmp_path)
        assert _result(tmp_path)["skipped"] == []

    def test_65535_arquivos_usam_registro_zip64(self, tmp_path):
        import io
        import zipfile
        raw = _build(tmp_path, files=[["docs/a.txt", "hello"]], empty=0xFFFE)
        assert b"PK\x06\x06" in raw
        zf = zipfile.ZipFile(io.BytesIO(raw))
        assert len(zf.infolist()) == 0xFFFF
        assert zf.read("docs/a.txt") == b"hello"
        assert zf.read("docs/e65533.txt") == b""
