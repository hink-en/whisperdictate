"""Read this process's effective permissions, without prompting or changing them."""
from ApplicationServices import AXIsProcessTrusted
from Quartz import CGPreflightListenEventAccess


def keyboard_permissions():
    return bool(AXIsProcessTrusted()), bool(CGPreflightListenEventAccess())
