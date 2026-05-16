import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


def test_is_url_true():
    from download import is_url
    assert is_url("https://youtube.com/watch?v=abc123") is True
    assert is_url("http://example.com/video.mp4") is True


def test_is_url_false():
    from download import is_url
    assert is_url("/path/to/video.mp4") is False
    assert is_url("relative/path.mp4") is False


def test_get_slug_from_title():
    from download import get_slug
    assert get_slug("How I Built X With Claude Code") == "how-i-built-x-with-claude-code"
    assert get_slug("Test! @Video #123") == "test-video-123"


def test_local_file_passthrough(tmp_path):
    from download import download_video
    video = tmp_path / "test.mp4"
    video.write_bytes(b'\x00' * 100)
    result = download_video(str(video), str(tmp_path))
    assert result['video_path'] == str(video)
    assert result['is_local'] is True


def test_download_rejects_missing_file():
    from download import download_video
    import pytest
    with pytest.raises(FileNotFoundError):
        download_video("/nonexistent/video.mp4", "/tmp")
