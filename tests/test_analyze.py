import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


def test_parse_args_url():
    from analyze import parse_args
    args = parse_args(['https://youtube.com/watch?v=test'])
    assert args.source == 'https://youtube.com/watch?v=test'
    assert args.out_dir == '.'
    assert args.max_frames == 80
    assert args.no_whisper is False


def test_parse_args_local():
    from analyze import parse_args
    args = parse_args(['/path/to/video.mp4', '--out-dir', '/output'])
    assert args.source == '/path/to/video.mp4'
    assert args.out_dir == '/output'


def test_parse_args_flags():
    from analyze import parse_args
    args = parse_args([
        'https://example.com/v',
        '--max-frames', '40',
        '--no-whisper',
        '--low-res',
        '--whisper', 'groq',
    ])
    assert args.max_frames == 40
    assert args.no_whisper is True
    assert args.low_res is True
    assert args.whisper == 'groq'


def test_parse_args_force_long():
    from analyze import parse_args
    args = parse_args(['test.mp4', '--force-long'])
    assert args.force_long is True


def test_get_cache_dir():
    from analyze import get_cache_dir
    import shutil
    d = get_cache_dir()
    assert '.cache/video-analyzer/' in d
    assert os.path.isdir(d)
    # Cleanup
    shutil.rmtree(d, ignore_errors=True)
