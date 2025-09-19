import unittest
from eventflow_cli.main import make_parser

class TestCLISmoke(unittest.TestCase):
    def test_subcommands_exist(self):
        p = make_parser()
        subs = {a.dest for a in p._subparsers._group_actions[0]._name_parser_map.values()}
        # name_parser_map preserves mapping; ensure known names exist
        names = set(p._subparsers._group_actions[0]._name_parser_map.keys())
        for cmd in ("build","run","profile","validate"):
            self.assertIn(cmd, names)
