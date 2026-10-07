import json, sys, unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from scripts import local_team as team

CODEX = json.dumps({'models': [
    {'slug': 'gpt-6.1-sol', 'description': 'workhorse', 'visibility': 'list', 'supported_reasoning_levels': [{'effort': e} for e in ('low', 'medium', 'high', 'xhigh')]},
    {'slug': 'gpt-6-luna', 'description': 'fast', 'visibility': 'list', 'supported_reasoning_levels': [{'effort': e} for e in ('low', 'medium')]},
    {'slug': 'codex-auto-review', 'description': 'hidden', 'visibility': 'hide', 'supported_reasoning_levels': [{'effort': 'medium'}]}]})
CLAUDE = json.dumps({'catalog': {'config': {'models': [
    {'id': 'claude-sonnet-5-5', 'description': 'efficient', 'section': 'main', 'thinking': {'type': 'effort', 'effort_options': [{'id': 'low'}, {'id': 'medium'}, {'id': 'high'}]}},
    {'id': 'claude-opus-5-5', 'description': 'complex', 'section': 'main', 'thinking': {'type': 'effort', 'effort_options': [{'id': 'medium'}, {'id': 'high'}]}},
    {'id': 'claude-fable-5-1', 'description': 'toughest', 'section': 'main', 'badge': {'message': 'Requires usage credits'}, 'thinking': {'type': 'effort', 'effort_options': [{'id': 'high'}]}},
    {'id': 'claude-haiku-4-5', 'name': 'Haiku', 'section': 'main', 'thinking': {'type': 'none'}},
    {'id': 'claude-opus-4-6', 'section': 'overflow', 'thinking': {'type': 'effort', 'effort_options': [{'id': 'high'}]}}]}}})


def catalogs():
    codex, claude = team.parse_codex_catalog(CODEX), team.parse_claude_catalog(CLAUDE)
    return {'plan': codex, 'validate': codex, 'implement': claude, 'review': claude}


def models(**stages):
    base = {'plan': ('gpt-6.1-sol', 'medium'), 'implement': ('claude-sonnet-5-5', 'medium'),
            'validate': ('gpt-6-luna', 'medium'), 'review': ('claude-opus-5-5', 'medium')}
    base.update(stages)
    return {k: {'model': m, 'effort': e} for k, (m, e) in base.items()}


class ModelCatalogTests(unittest.TestCase):
    def test_catalog_parsers_keep_efforts_and_visibility(self):
        codex, claude = team.parse_codex_catalog(CODEX), team.parse_claude_catalog(CLAUDE)
        self.assertEqual(codex['gpt-6-luna']['efforts'], ['low', 'medium']); self.assertFalse(codex['codex-auto-review']['listed'])
        self.assertEqual(claude['claude-haiku-4-5']['efforts'], []); self.assertFalse(claude['claude-opus-4-6']['listed'])
        self.assertTrue(claude['claude-sonnet-5-5']['listed'])

    def test_valid_configuration_passes(self):
        self.assertEqual({lvl for _, lvl, _ in team.check_models(models(), catalogs())}, {'ok'})

    def test_typos_wrong_case_and_foreign_family_are_caught_with_a_hint(self):
        rows = {s: (lvl, msg) for s, lvl, msg in team.check_models(models(validate=('gpt-6-Luna', 'medium'), review=('claude-terra', 'medium')), catalogs())}
        self.assertEqual(rows['validate'][0], 'error'); self.assertIn('did you mean: gpt-6-luna', rows['validate'][1])
        self.assertEqual(rows['review'][0], 'error'); self.assertIn('claude-terra is not an available claude model', rows['review'][1])
        self.assertIn('claude-', rows['review'][1].split('did you mean')[-1])  # suggestions stay within the provider's catalog
        with patch.object(team, 'read_stage_catalog', side_effect=lambda kind: catalogs()[kind]):
            with self.assertRaises(team.Blocked) as ctx:
                team.require_valid_models(models(review=('claude-terra', 'medium')))
        self.assertIn('review:', str(ctx.exception))

    def test_credit_billed_models_are_refused_and_never_suggested(self):
        self.assertTrue(team.parse_claude_catalog(CLAUDE)['claude-fable-5-1']['credits'])
        rows = {s: (lvl, msg) for s, lvl, msg in team.check_models(models(review=('claude-fable-5-1', 'high'), implement=('claude-terra', 'medium')), catalogs())}
        self.assertEqual(rows['review'][0], 'error'); self.assertIn('never changes billing', rows['review'][1])
        self.assertNotIn('fable', rows['implement'][1])

    def test_unsupported_effort_and_no_effort_control(self):
        rows = {s: (lvl, msg) for s, lvl, msg in team.check_models(models(validate=('gpt-6-luna', 'xhigh'), implement=('claude-haiku-4-5', 'high')), catalogs())}
        self.assertEqual(rows['validate'][0], 'error'); self.assertIn("effort 'xhigh'", rows['validate'][1]); self.assertIn('low, medium', rows['validate'][1])
        self.assertEqual(rows['implement'][0], 'warn'); self.assertIn('no effort control', rows['implement'][1])

    def test_hidden_models_warn_and_missing_catalog_never_blocks(self):
        rows = {s: lvl for s, lvl, _ in team.check_models(models(plan=('codex-auto-review', 'medium')), catalogs())}
        self.assertEqual(rows['plan'], 'warn')
        unknown = {k: None for k in team.STAGES}
        self.assertEqual({lvl for _, lvl, _ in team.check_models(models(), unknown)}, {'warn'})
        with patch.object(team, 'read_stage_catalog', return_value=None):
            team.require_valid_models(models())  # unverifiable is a warning, not a failure

    def test_models_view_lists_configuration_and_availability(self):
        with patch.object(team, 'read_stage_catalog', side_effect=lambda kind: catalogs()[kind]):
            text = team.render_models(models(review=('claude-terra', 'medium')))
        self.assertIn('✖ review', text); self.assertIn('✔ plan', text); self.assertIn('DISPONÍVEIS (codex)', text)
        self.assertIn('gpt-6-luna', text); self.assertNotIn('codex-auto-review', text)


if __name__ == '__main__':
    unittest.main()
