import os
import pwd


def get_username():
    try:
        res = pwd.getpwuid(os.getuid())[0]
        assert isinstance(res, str) and res
        return res
    except Exception:
        return os.getlogin()
