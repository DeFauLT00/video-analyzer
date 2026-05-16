import subprocess
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


def test_check_binary_found():
    """check_binary returns True for a binary that exists."""
    from preflight import check_binary
    assert check_binary('python3') is True


def test_check_binary_not_found():
    """check_binary returns False for a binary that doesn't exist."""
    from preflight import check_binary
    assert check_binary('nonexistent_binary_xyz') is False


def test_check_api_key_present(tmp_path):
    """check_api_keys finds keys in env file."""
    from preflight import check_api_keys
    env_file = tmp_path / ".env"
    env_file.write_text("GOOGLE_API_KEY=test123\n")
    result = check_api_keys(str(env_file))
    assert result['GOOGLE_API_KEY'] is True


def test_check_api_key_missing(tmp_path):
    """check_api_keys reports missing keys."""
    from preflight import check_api_keys
    env_file = tmp_path / ".env"
    env_file.write_text("GROQ_API_KEY=test\n")
    result = check_api_keys(str(env_file))
    assert result['GOOGLE_API_KEY'] is False


def test_preflight_check_returns_status():
    """preflight_check returns a dict with binaries and keys status."""
    from preflight import preflight_check
    result = preflight_check(env_path='/tmp/nonexistent/.env')
    assert 'binaries' in result
    assert 'keys' in result
    assert 'ready' in result
