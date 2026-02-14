# Import the example driver to test its helper dynamically (examples is not a package)
import importlib.util
import sys
from pathlib import Path

from .test_c_generator import build_sample_db  # reuse builder


def _load_examples_cgen():
    root = Path(__file__).resolve().parents[2]
    mod_path = root / "examples" / "cgen.py"
    spec = importlib.util.spec_from_file_location("examples_cgen", mod_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_examples_cgen_run_on_prgdb_writes_output(tmp_path):
    db_path = tmp_path / "sample.prgdb"
    # Build a small DB on disk
    db, cu = build_sample_db(str(db_path))
    try:
        out_path = tmp_path / "out.h"
        mod = _load_examples_cgen()
        rc = mod.run_on_prgdb(str(db_path), start_offset=None, out=str(out_path))
        assert rc == 0
        assert out_path.exists()
        content = out_path.read_text(encoding="utf-8")
        # Spot-check a few declarations
        assert "typedef enum Color" in content
        assert "typedef struct Point" in content
        assert "typedef int MyInt;" in content or "typedef base_type MyInt;" in content
    finally:
        db.close()
