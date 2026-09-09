# -*- coding: utf-8 -*-
"""Entry point executed *inside* FreeCADCmd for the console test-suite.

Usage:
  freecadcmd -P <repo> -u <tmp>/user.cfg -s <tmp>/system.cfg \\
             -c "exec(open('tests/fc/run_all.py').read())"
"""
import importlib
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
for p in (REPO,):
    if p not in sys.path:
        sys.path.insert(0, p)

MODULES = [
    "test_imports_and_prefs",
    "test_model_flow",
    "test_exporters",
    "test_reference_images",
    "test_examples_models",
    "test_nav_and_commands",
]


def main():
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for name in MODULES:
        path = os.path.join(HERE, name + ".py")
        if not os.path.isfile(path):
            print("missing module", name)
            continue
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        suite.addTests(loader.loadTestsFromModule(mod))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print("FREECAD_CONSOLE_TESTS summary: run=%d failures=%d errors=%d"
          % (result.testsRun, len(result.failures), len(result.errors)))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
