import ryvencore as rc
import unittest


def check_addon_available(addon_name: str, test_name: str):
    try:
        s = rc.Session(load_addons=True)
        addon = s.addons[addon_name]
    except KeyError:
        raise unittest.SkipTest(
            f'{addon_name} AddOn not available. '
            f'Skipping all tests in {test_name}')
