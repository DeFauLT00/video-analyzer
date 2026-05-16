import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


def test_extract_audio_command():
    """Verify the ffmpeg command is constructed correctly."""
    from whisper import _build_audio_extract_cmd
    cmd = _build_audio_extract_cmd("/path/to/video.mp4", "/tmp/audio.wav")
    assert 'ffmpeg' in cmd[0]
    assert '-ar' in cmd
    assert '16000' in cmd
    assert '/tmp/audio.wav' in cmd


def test_select_backend_groq():
    """Auto-selects groq when GROQ_API_KEY is available."""
    from whisper import select_backend
    keys = {'GROQ_API_KEY': True, 'OPENAI_API_KEY': False}
    assert select_backend('auto', keys) == 'groq'


def test_select_backend_openai_fallback():
    """Falls back to openai when groq unavailable."""
    from whisper import select_backend
    keys = {'GROQ_API_KEY': False, 'OPENAI_API_KEY': True}
    assert select_backend('auto', keys) == 'openai'


def test_select_backend_none():
    """Returns None when no keys available."""
    from whisper import select_backend
    keys = {'GROQ_API_KEY': False, 'OPENAI_API_KEY': False}
    assert select_backend('auto', keys) is None


def test_select_backend_forced():
    """Respects forced backend selection."""
    from whisper import select_backend
    keys = {'GROQ_API_KEY': True, 'OPENAI_API_KEY': True}
    assert select_backend('openai', keys) == 'openai'
