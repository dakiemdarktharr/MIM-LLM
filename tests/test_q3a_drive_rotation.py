"""A real resume exposed stale local previous.pt overwriting remote rotation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_q3a_colab import sync_run_files


def test_stale_restored_backup_cannot_replace_last_synced_checkpoint(tmp_path):
    local, remote = tmp_path / "local", tmp_path / "remote"
    local.mkdir()
    remote.mkdir()
    (local / "latest.pt").write_bytes(b"new-local-checkpoint")
    (local / "previous.pt").write_bytes(b"stale-restored-backup")
    (remote / "latest.pt").write_bytes(b"previous-successful-sync")
    (remote / "previous.pt").write_bytes(b"older-remote-backup")
    hashes = sync_run_files(local, remote)
    assert (remote / "previous.pt").read_bytes() == b"previous-successful-sync"
    assert (remote / "latest.pt").read_bytes() == b"new-local-checkpoint"
    assert "previous.pt" in hashes
    sync_run_files(local, remote)
    assert (remote / "previous.pt").read_bytes() == b"previous-successful-sync"


def test_new_remote_does_not_publish_stale_local_backup(tmp_path):
    local, remote = tmp_path / "local", tmp_path / "remote"
    local.mkdir()
    (local / "latest.pt").write_bytes(b"first-real-checkpoint")
    (local / "previous.pt").write_bytes(b"stale-backup")
    hashes = sync_run_files(local, remote)
    assert (remote / "latest.pt").read_bytes() == b"first-real-checkpoint"
    assert not (remote / "previous.pt").exists()
    assert "previous.pt" not in hashes
