"""Persistence unit fixtures, not real model checkpoints or training."""

import importlib.util
from pathlib import Path

import pytest


def module():
    spec = importlib.util.spec_from_file_location(
        "colab_runner", Path("scripts/run_q3a_colab.py")
    )
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def test_verified_latest_keeps_previous(tmp_path):
    m = module()
    source, target = tmp_path / "source", tmp_path / "remote/latest.pt"
    source.write_bytes(b"UNIT first checkpoint")
    m.verified_copy(source, target, keep_previous=True)
    source.write_bytes(b"UNIT next checkpoint")
    m.verified_copy(source, target, keep_previous=True)
    assert target.read_bytes() == source.read_bytes()
    assert (target.parent / "previous.pt").read_bytes() == b"UNIT first checkpoint"


def test_bad_upload_preserves_latest(tmp_path, monkeypatch):
    m = module()
    source, target = tmp_path / "source", tmp_path / "latest.pt"
    source.write_bytes(b"UNIT new")
    target.write_bytes(b"UNIT retained")
    monkeypatch.setattr(
        m.shutil, "copyfile", lambda s, t: Path(t).write_bytes(b"BAD UPLOAD")
    )
    with pytest.raises(OSError, match="reread hash mismatch"):
        m.verified_copy(source, target, keep_previous=True)
    assert target.read_bytes() == b"UNIT retained"
