"""
MicroPython-dotenv MICRO
Ultra-lightweight version (~2KB) for memory-constrained devices

Only includes essential functionality.
For full version, use dotenv.py
"""

__version__ = '1.0.0-micro'

# MicroPython doesn't have os.environ, create our own
_environ = {}


def load_dotenv(path='.env'):
    """Load .env file into environment. Returns dict."""
    global _environ
    try:
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    k, v = k.strip(), v.strip()
                    # Remove quotes
                    if len(v) >= 2 and ((v[0] == '"' == v[-1]) or (v[0] == "'" == v[-1])):
                        v = v[1:-1]
                    _environ[k] = v
    except Exception as e:
        print(f"Warning: Could not load .env file: {e}")
    return _environ


def get_env(key, default=None):
    """Get environment variable with default."""
    return _environ.get(key, default)
