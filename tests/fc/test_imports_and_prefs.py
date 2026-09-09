# -*- coding: utf-8 -*-
"""Console tests - package imports, prefs store & backups (no GUI needed)."""
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

import FreeCAD  # noqa: E402


class TestImports(unittest.TestCase):
    def test_core_modules_import(self):
        import opencad_ux  # noqa
        import opencad_ux.config  # noqa
        import opencad_ux.prefs  # noqa
        import opencad_ux.commands.registry  # noqa
        import opencad_ux.commands.adapters  # noqa
        import opencad_ux.commands.exporters  # noqa
        import opencad_ux.keymap.presets  # noqa
        import opencad_ux.keymap.conflicts  # noqa
        import opencad_ux.command_search.engine  # noqa
        import opencad_ux.context_menu  # noqa
        import opencad_ux.navigation  # noqa
        import opencad_ux.reference_images  # noqa
        self.assertTrue(True)

    def test_resources_exist(self):
        import opencad_ux.config as cfg

        self.assertTrue(os.path.isfile(cfg.RIBBON_SCHEMA))
        self.assertTrue(os.path.isfile(cfg.KEYMAP_PRESETS))
        self.assertTrue(os.path.isdir(cfg.ICONS_DIR))

    def test_fc_version_sane(self):
        v = FreeCAD.Version()[0:3]
        self.assertEqual(int(v[0]), 1)


class TestPrefsStore(unittest.TestCase):
    def test_settings_roundtrip(self):
        from opencad_ux import prefs

        prefs.reset_backend()  # will use FreeCAD param group in this process
        s = prefs.Settings()
        s.set_bool("TestBool", True)
        s.set_int("TestInt", 42)
        s.set_string("TestStr", "hello")
        s.set_list("TestList", ["a", "b"])
        self.assertTrue(s.get_bool("TestBool"))
        self.assertEqual(s.get_int("TestInt"), 42)
        self.assertEqual(s.get_string("TestStr"), "hello")
        self.assertEqual(s.get_list("TestList"), ["a", "b"])
        # cleanup
        for key in ("TestBool", "TestInt", "TestStr", "TestList"):
            try:
                s.store.RemoveBool(key) if hasattr(s.store, "RemoveBool") else None
                s.store.RemoveInt(key) if hasattr(s.store, "RemoveInt") else None
                s.store.RemoveFloat(key) if hasattr(s.store, "RemoveFloat") else None
                s.store.RemoveString(key) if hasattr(s.store, "RemoveString") else None
            except Exception:
                pass

    def test_backup_config_files(self):
        from opencad_ux import prefs

        # make sure the isolated user.cfg exists before backing it up
        grp = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/OpenCADUXTest")
        grp.SetBool("Dummy", True)
        FreeCAD.saveParameter()
        files = prefs.backup_config_files("selftest", "console test backup")
        self.assertTrue(len(files) >= 1)
        listing = prefs.list_backups("selftest")
        self.assertTrue(any(f in [x[0] for x in listing] for f in files))


if __name__ == "__main__":
    unittest.main(verbosity=2)
