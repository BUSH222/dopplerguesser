import getpass
import os


def get_username():
    try:
        res = getpass.getuser()
        assert isinstance(res, str) and res
        return res
    except Exception:
        return os.getlogin()
