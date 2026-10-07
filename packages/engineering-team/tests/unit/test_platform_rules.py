import json, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
import local_team as lt
from jsonschema import ValidationError

HANDOFF = {'registry_fingerprint': 'a' * 64, 'product': 'meu-site',
           'capabilities': [{'name': 'entitlements', 'decision': 'REUSE', 'owner': 'product-platform-harness'}]}


class PlatformRulesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.handoff = self.tmp / 'handoff.json'; self.handoff.write_text(json.dumps(HANDOFF))
        self.rules = self.tmp / 'DELIVERY.md'; self.rules.write_text('# regras')
        self.run_dir = self.tmp / 'run'; self.run_dir.mkdir()

    def freeze(self):
        return lt.freeze_platform(self.run_dir, lt.platform_inputs(str(self.handoff), [str(self.rules)]))

    def test_no_inputs_changes_nothing(self):
        self.assertEqual(lt.platform_inputs(None, []), {})
        self.assertIsNone(lt.freeze_platform(self.run_dir, {}))
        self.assertEqual(lt.with_platform('Request: x', {}), 'Request: x')
        self.assertEqual(lt.platform_artifacts(self.run_dir, {}), [])

    def test_invalid_handoff_is_rejected_before_any_task_exists(self):
        self.handoff.write_text(json.dumps({**HANDOFF, 'capabilities': [{'name': 'x', 'decision': 'COPY', 'owner': 'o'}]}))
        with self.assertRaises(ValidationError):
            lt.platform_inputs(str(self.handoff), [])

    def test_oversized_or_duplicate_rules_are_rejected(self):
        self.rules.write_text('x' * (lt.PLATFORM_MAX_BYTES + 1))
        with self.assertRaises(lt.Blocked):
            lt.platform_inputs(None, [str(self.rules)])
        self.rules.write_text('ok')
        other = self.tmp / 'sub'; other.mkdir(); (other / 'DELIVERY.md').write_text('outro')
        with self.assertRaises(lt.Blocked):
            lt.platform_inputs(None, [str(self.rules), str(other / 'DELIVERY.md')])

    def test_frozen_files_are_verified_and_tampering_blocks_the_stage(self):
        state = {'platform': self.freeze()}
        names = [n for n, _ in lt.platform_artifacts(self.run_dir, state)]
        self.assertEqual(sorted(names), ['capabilities.json', 'rules/DELIVERY.md'])
        frozen = self.run_dir / 'platform/rules/DELIVERY.md'; frozen.chmod(0o600); frozen.write_text('enfraquecida')
        with self.assertRaises(lt.Blocked):
            lt.platform_artifacts(self.run_dir, state)

    def test_prompt_cites_platform_rules_once_before_the_request(self):
        state = {'platform': self.freeze()}
        for marker in ('Original request: ', 'Request: '):
            out = lt.with_platform(f'Do X. {marker}pedido', state)
            self.assertLess(out.index('Platform delivery rules'), out.index(marker))
            self.assertIn('/handoff/rules/', out)
            self.assertEqual(lt.with_platform(out, state), out)


ENVELOPE = json.loads((Path(__file__).resolve().parents[3] / 'kit/contracts/platform-handoff/fixtures/valid.json').read_text())
PROPOSAL_BASE = ENVELOPE['proposal']['repository']['base_sha']


class EnvelopeHandoffTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.run_dir = self.tmp / 'run'; self.run_dir.mkdir()

    def write(self, value):
        path = self.tmp / 'envelope.json'; path.write_text(json.dumps(value)); return str(path)

    def test_envelope_is_split_into_the_files_the_stages_read(self):
        inputs = lt.platform_inputs(self.write(ENVELOPE), [], None, PROPOSAL_BASE)
        self.assertEqual(sorted(inputs), ['capabilities.json', 'proposal.json', 'rules.json'])
        self.assertEqual(json.loads(inputs['capabilities.json']), ENVELOPE['portfolio'])  # formato que o gate do plano usa
        self.assertEqual(json.loads(inputs['proposal.json'])['objective'], ENVELOPE['proposal']['objective'])
        self.assertEqual(json.loads(inputs['rules.json'])['profile'], 'backend')
        state = {'platform': lt.freeze_platform(self.run_dir, inputs)}
        self.assertEqual(sorted(n for n, _ in lt.platform_artifacts(self.run_dir, state)), sorted(inputs))
        self.assertIn('/handoff/proposal.json', lt.with_platform('Request: x', state))

    def test_floating_refs_and_unknown_fields_are_rejected_by_the_kit_schema(self):
        floating = json.loads(json.dumps(ENVELOPE)); floating['rules_refs']['kit']['ref'] = 'main'
        extra = dict(ENVELOPE, surprise=1)
        for bad in (floating, extra):
            with self.assertRaises(ValidationError):
                lt.platform_inputs(self.write(bad), [], None, PROPOSAL_BASE)

    def test_stale_proposal_is_blocked_by_base_sha_but_unknown_head_is_not_checked(self):
        with self.assertRaises(lt.Blocked):
            lt.platform_inputs(self.write(ENVELOPE), [], None, 'f' * 40)
        self.assertIn('proposal.json', lt.platform_inputs(self.write(ENVELOPE), [], None, None))
        no_base = json.loads(json.dumps(ENVELOPE)); del no_base['proposal']['repository']['base_sha']
        self.assertIn('proposal.json', lt.platform_inputs(self.write(no_base), [], None, 'f' * 40))

    def test_registry_check_uses_the_envelope_portfolio_fingerprint(self):
        registry = self.tmp / 'registry.yaml'; registry.write_text('capabilities: {}')
        with self.assertRaises(lt.Blocked):  # o fixture guarda um fingerprint de referência
            lt.platform_inputs(self.write(ENVELOPE), [], str(registry), PROPOSAL_BASE)
        matching = json.loads(json.dumps(ENVELOPE))
        matching['portfolio']['registry_fingerprint'] = __import__('hashlib').sha256(registry.read_bytes()).hexdigest()
        self.assertIn('rules.json', lt.platform_inputs(self.write(matching), [], str(registry), PROPOSAL_BASE))


if __name__ == '__main__':
    unittest.main()
