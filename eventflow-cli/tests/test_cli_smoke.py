import unittest
from eventflow_cli.main import make_parser

class TestCLISmoke(unittest.TestCase):
    def test_subcommands_exist(self):
        p = make_parser()
        # Ensure known subcommand names exist
        names = set(p._subparsers._group_actions[0]._name_parser_map.keys())
        for cmd in ("build", "run", "profile", "validate"):
            self.assertIn(cmd, names)
