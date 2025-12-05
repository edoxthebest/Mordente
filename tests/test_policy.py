import logging
import subprocess
import unittest
from pathlib import Path

from selinuxtool.android.policy import Policy
from selinuxtool.util.common import nfa_to_word


class TestPolicySecurityDiffs(unittest.TestCase):
    def setUp(self) -> None:
        self.logger = logging.getLogger('SELinuxTool')
        self.logger.setLevel(logging.DEBUG)
        return super().setUp()

    def compile_policies(self, cilA: str, cilB: str) -> None:
        common_path = Path('policies/tests')
        pathA = common_path / 'A'
        pathB = common_path / 'B'

        subprocess.run(
            [
                'secilc',
                str(common_path / cilA),
                '-o',
                str(pathA / 'precompiled_sepolicy'),
                '-f',
                '/dev/null',
            ]
        )
        subprocess.run(
            [
                'secilc',
                str(common_path / cilB),
                '-o',
                str(pathB / 'precompiled_sepolicy'),
                '-f',
                '/dev/null',
            ]
        )

    def init(self, cilA: str, cilB: str) -> None:
        self.compile_policies(cilA, cilB)
        self.policyA = Policy(Path('policies/tests/A'))
        self.policyB = Policy(Path('policies/tests/B'))
        self.policyA.load_policy(False, False, 0)
        self.policyB.load_policy(False, False, 1)

    def test_no_diff(self) -> None:
        self.init('untrusted_to_critical.cil', 'untrusted_to_critical.cil')

        label_diffs, _ = self.policyA.security_lvs_diff(self.policyB)
        self.assertFalse(label_diffs)

    def test_A_missing_critical(self) -> None:
        self.init('missing_critical.cil', 'untrusted_to_critical.cil')

        label_diffs, _ = self.policyA.security_lvs_diff(self.policyB)
        self.assertTrue(label_diffs)
        self.assertEqual(label_diffs, {'isolated2'})

    def test_A_missing_untrusted(self) -> None:
        self.init('missing_untrusted.cil', 'untrusted_to_critical.cil')

        label_diffs, _ = self.policyA.security_lvs_diff(self.policyB)
        self.assertTrue(label_diffs)
        self.assertEqual(label_diffs, {'isolated1'})

    def test_A_not_reaching_critical(self) -> None:
        self.init('untrusted_to_safe.cil', 'untrusted_to_critical.cil')

        label_diffs, _ = self.policyA.security_lvs_diff(self.policyB)
        self.assertTrue(label_diffs)
        self.assertEqual(label_diffs, {'isolated1', 'isolated2'})

    def test_A_no_fc(self) -> None:
        self.init('untrusted_to_critical.cil', 'untrusted_to_critical.cil')

        label_diffs, fc_diffs = self.policyA.security_lvs_diff(self.policyB)
        self.assertFalse(label_diffs)
        self.assertEqual(nfa_to_word(fc_diffs)[0], '/file1')
