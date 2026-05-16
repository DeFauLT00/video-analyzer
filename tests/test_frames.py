import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


def test_timestamp_to_seconds():
    from frames import timestamp_to_seconds
    assert timestamp_to_seconds("00:00") == 0
    assert timestamp_to_seconds("01:30") == 90
    assert timestamp_to_seconds("1:00:00") == 3600
    assert timestamp_to_seconds("00:05") == 5


def test_build_ffmpeg_command():
    from frames import _build_frame_cmd
    cmd = _build_frame_cmd("/video.mp4", 30.0, "/out/frame-001.jpg", 512)
    assert 'ffmpeg' in cmd[0]
    assert '-ss' in cmd
    assert '30.0' in cmd
    assert '/out/frame-001.jpg' in cmd


def test_select_timestamps_under_max():
    from frames import select_timestamps
    timestamps = [0, 10, 20, 30, 40]
    result = select_timestamps(timestamps, max_frames=80)
    assert result == timestamps


def test_select_timestamps_over_max():
    from frames import select_timestamps
    timestamps = list(range(100))
    result = select_timestamps(timestamps, max_frames=10)
    assert len(result) == 10
    assert result[0] == 0
    assert result[-1] == 99


def test_get_frame_filename():
    from frames import get_frame_filename
    assert get_frame_filename(0) == "frame-001.jpg"
    assert get_frame_filename(9) == "frame-010.jpg"
    assert get_frame_filename(99) == "frame-100.jpg"
