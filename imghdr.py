# Minimal stub so libraries that import `imghdr` keep working on Python 3.13+
# Your bot doesn't rely on image type detection, so this is enough.

def what(file, h=None):
    # We don't try to detect anything, just say "unknown"
    return None
