"""Read-only insight into an ai-team task: what each stage does, live activity, plan, changes, tests, reviews.

Shared by `ai-team watch` (text), `report`/`serve` (HTML), `logs` and `history`. Everything read from a task
directory is untrusted agent output: it is only displayed (HTML-escaped), never executed.
"""
import html
import json
import re
import subprocess
import time
from pathlib import Path

PIPELINE = ('plan', 'implement', 'tests', 'validate', 'review')
STAGE_INFO = {
    'plan': ('Atlas · Planejar', 'Lê o repositório (somente leitura) e propõe tarefas e critérios de aceite. Não edita nada.'),
    'implement': ('Argus · Implementar', 'Edita os arquivos conforme o plano e registra o OpenSpec. Não roda testes nem faz commit.'),
    'tests': ('Host · Testes offline', 'Roda os checks configurados em container sem rede e sem credenciais.'),
    'validate': ('Sentinel · Validar', 'Verifica de forma independente se diff e testes atendem a cada critério do plano.'),
    'review': ('Atlas · Revisar', 'Segunda revisão em sessão nova: veredito por critério e achados por severidade.'),
}
PHASE_STEP = {'PLAN': 'plan', 'IMPLEMENT': 'implement', 'TEST': 'tests', 'REVIEW': 'review'}
ICON = {'done': '✔', 'running': '▶', 'failed': '✖', 'pending': '·'}
TERMINAL = {'REVIEWED', 'DELIVERED', 'FAILED', 'STOPPED', 'INTERRUPTED'}


def fmt_s(seconds):
    seconds = max(0, int(seconds))
    h, rest = divmod(seconds, 3600)
    m, s = divmod(rest, 60)
    return f'{h}h{m:02d}m' if h else f'{m}m{s:02d}s' if m else f'{s}s'


def short(text, n=100):
    text = ' '.join(str(text).split())
    return text if len(text) <= n else text[:n - 1] + '…'


def jsonl(path):
    """Events of a provider log: JSONL, or a single JSON array (old claude format)."""
    try:
        text = path.read_text(errors='replace')
    except OSError:
        return []
    events = []
    if text.lstrip().startswith('['):
        try:
            events = json.loads(text)
        except ValueError:
            pass
    else:
        for line in text.splitlines():
            try:
                events.append(json.loads(line))
            except ValueError:
                pass
    return [e for e in events if isinstance(e, dict)]


def usage(path):
    """Tokens/cost from a provider log. Claude: authoritative `result`, else live sum of assistant messages."""
    out = {'events': 0, 'in': 0, 'out': 0, 'cost': None, 'cached': 0}
    events = jsonl(path)
    out['events'] = len(events)
    per_message, result = {}, None
    for e in events:
        u = e.get('usage') or {}
        if e.get('type') == 'turn.completed' and u:  # codex
            out['in'] += u.get('input_tokens', 0)
            out['out'] += u.get('output_tokens', 0)
            out['cached'] += u.get('cached_input_tokens', 0)
        elif e.get('type') == 'result':
            result = e
        elif e.get('type') == 'assistant' and isinstance(e.get('message'), dict):
            mu = e['message'].get('usage') or {}
            per_message[e['message'].get('id') or len(per_message)] = mu
    if result:
        u = result.get('usage') or {}
        out['in'] += u.get('input_tokens', 0) + u.get('cache_read_input_tokens', 0) + u.get('cache_creation_input_tokens', 0)
        out['out'] += u.get('output_tokens', 0)
        out['cached'] += u.get('cache_read_input_tokens', 0)
        out['cost'] = result.get('total_cost_usd')
    else:
        for u in per_message.values():
            out['in'] += u.get('input_tokens', 0) + u.get('cache_read_input_tokens', 0) + u.get('cache_creation_input_tokens', 0)
            out['out'] += u.get('output_tokens', 0)
    return out


def _path(value):
    return str(value).replace('/work/', '').replace('/handoff/', 'handoff/')


def describe(event):
    """One human sentence per provider event, or None for noise."""
    kind = event.get('type')
    item = event.get('item') or {}
    if kind == 'item.started' and item.get('type') == 'command_execution':
        cmd = re.sub(r'^/bin/(ba)?sh -lc ', '', item.get('command', ''))
        return '▸ ' + short(cmd, 110)
    if kind == 'item.completed' and item.get('type') == 'agent_message':
        return '💬 ' + short(item.get('text', ''), 150)
    if kind == 'item.completed' and item.get('type') == 'file_change':
        return '✏️  arquivos alterados: ' + short(', '.join(_path(c.get('path', '')) for c in item.get('changes', [])), 110)
    if kind == 'assistant' and isinstance(event.get('message'), dict):
        parts = []
        for block in event['message'].get('content') or []:
            if block.get('type') == 'text' and block.get('text', '').strip():
                parts.append('💬 ' + short(block['text'], 150))
            elif block.get('type') == 'tool_use':
                name, inp = block.get('name'), block.get('input') or {}
                target = _path(inp.get('file_path') or inp.get('path') or inp.get('pattern') or '')
                verb = {'Read': '📖 lendo', 'Edit': '✏️  editando', 'Write': '✏️  escrevendo', 'Glob': '🔎 buscando arquivos',
                        'Grep': '🔎 buscando texto', 'StructuredOutput': '📦 devolvendo o resultado'}.get(name, name)
                parts.append(f'{verb} {target}'.strip())
        return '\n'.join(parts) or None
    return None


def run_label(run):
    """Log/dir label of a stage run: '<cycle>-<stage>' or '<cycle>p<part>-<stage>' for later parts of a split stage."""
    return run.get('label') or f"{run['cycle']}-{run['stage']}"


def _label_key(name):
    m = re.match(r'(\d+)(?:p(\d+))?-', name)
    return (int(m.group(1)), int(m.group(2) or 1)) if m else (0, 0)


def stage_log(path, stage, cycle=None):
    files = sorted(path.glob(f'*-{stage}.stdout'), key=lambda p: _label_key(p.name))
    if cycle is not None:
        files = [f for f in files if _label_key(f.name)[0] == cycle]
    return files[-1] if files else None


def active_stage(state):
    container = (state.get('active') or {}).get('container') or ''
    for name in PIPELINE:
        if container.endswith('-' + name):
            return name
    return None


def feed(path, state, n=8, stage=None):
    stage = stage or active_stage(state) or (state['stage_runs'][-1]['stage'] if state.get('stage_runs') else None)
    log = stage_log(path, stage) if stage else None
    if not log:
        return stage, []
    if stage == 'tests':
        return stage, [short(x, 110) for x in log.read_text(errors='replace').splitlines() if x.strip()][-n:]
    lines = [line for e in jsonl(log) if (d := describe(e)) for line in d.split('\n')]
    return stage, lines[-n:]


def stage_started(path, run):
    """Recorded start, or (older tasks) the mtime of the stage's stderr, which is created at launch."""
    if run.get('started_at'):
        return run['started_at']
    try:
        return (path / f"{run_label(run)}.stderr").stat().st_mtime
    except OSError:
        return None


def steps(state, path=None):
    """[(name, status, seconds|None)] for the five stages of the current task."""
    active = active_stage(state)
    failed = None
    if state['status'] in ('FAILED', 'STOPPED', 'INTERRUPTED') and not active:
        failed = PHASE_STEP.get(state['phase'])
        if failed == 'review' and state.get('stage_runs'):
            failed = state['stage_runs'][-1]['stage'] if state['stage_runs'][-1]['stage'] in ('validate', 'review') else 'validate'
    out = []
    for name in PIPELINE:
        runs = [r for r in state.get('stage_runs', []) if r['stage'] == name]
        if runs:  # a stage split in parts: aggregate the parts of its latest cycle
            latest = max(r['cycle'] for r in runs)
            runs = [r for r in runs if r['cycle'] == latest]
        ev = state.get('test_evidence') if name == 'tests' else None
        last = runs[-1] if runs else ev
        seconds = None
        if last:
            start = (min((stage_started(path, r) or time.time() for r in runs)) if path else last.get('started_at')) if runs else last.get('started_at')
            end = last.get('ended_at')
            if not end and path and name != active:
                log = path / f"{run_label(last)}.stdout" if runs else path / f"{last.get('cycle', 0)}-{name}.stdout"
                end = log.stat().st_mtime if log.exists() else None
            if start:
                seconds = (end or time.time()) - start
        if name == active:
            status = 'running'
        elif name == failed or (ev and ev.get('exit_code')):
            status = 'failed'
        elif runs or ev:
            status = 'done'
        else:
            status = 'pending'
        out.append((name, status, seconds))
    return out


def stage_cycle(log):
    return _label_key(log.name)[0]


def stage_prompt(path, state, stage, cycle=None, label=None):
    """Prompt a stage received: the saved file, or (older tasks) the running container's command line."""
    cycle = state['cycle'] if cycle is None else cycle
    if label is None and stage == active_stage(state):  # current session of a split stage
        run = next((r for r in reversed(state.get('stage_runs', [])) if r['stage'] == stage), None)
        label = run_label(run) if run else None
    saved = path / f'{label or f"{cycle}-{stage}"}.prompt'
    if saved.exists():
        return saved.read_text(errors='replace')
    container = (state.get('active') or {}).get('container')
    if container and container.endswith('-' + stage):
        try:
            r = subprocess.run(['docker', 'inspect', '--format', '{{json .Config.Cmd}}', container],
                               capture_output=True, text=True, timeout=10)
            cmd = json.loads(r.stdout)
        except (OSError, subprocess.TimeoutExpired, ValueError):
            return None
        for flag in ('-p',):  # claude -p <prompt>; codex puts the prompt last
            if flag in cmd and cmd.index(flag) + 1 < len(cmd):
                return cmd[cmd.index(flag) + 1]
        return cmd[-1] if cmd else None
    return None


def prompt_view(prompt, request):
    """(instruction text, extra sections) with the user's request collapsed: it is already in the header."""
    text = ' '.join(prompt.split())
    m = re.search(r' (?:Original request|Request): ', text)
    head, sep = (text[:m.start()], True) if m else (text, False)
    feedback = ''
    if 'Previous validation/review feedback:' in text:
        head, _, feedback = head.partition('Previous validation/review feedback:')
    return head.strip() + (' [Pedido: igual ao do cabeçalho]' if sep and request.strip() in text else ''), feedback.strip()


def feedback_items(state):
    """What the agent is being asked to fix in this cycle: open findings or failing tests of the previous cycle."""
    items = []
    for fb in state.get('feedback') or []:
        if not isinstance(fb, dict):
            continue
        if 'tests' in fb:
            items.append('TESTES FALHARAM: ' + short(fb.get('output', '').strip().splitlines()[-1:] or '', 100))
        for f in fb.get('findings', []):
            if f.get('status') == 'OPEN':
                items.append(f"{f['severity']}: {f['summary']}")
        for r in fb.get('acceptance_results', []):
            if r.get('status') != 'PASS':
                items.append(f"{r['id']} {r['status']}: {r.get('evidence', '')}")
    return items


def handoff_files(path, stage, cycle, label=None):
    d = path / f'handoff-{label or f"{cycle}-{stage}"}'
    return [(f.name, f.stat().st_size) for f in sorted(d.glob('*'))] if d.is_dir() else []


def wrap(text, width, max_lines):
    words, lines, cur = text.split(), [], ''
    for w in words:
        if len(cur) + len(w) + 1 > width and cur:
            lines.append(cur); cur = w
        else:
            cur = (cur + ' ' + w).strip()
    if cur:
        lines.append(cur)
    return lines[:max_lines - 1] + [lines[max_lines - 1] + ' …'] if len(lines) > max_lines else lines


def container_stats(container):
    """{'cpu','mem','net'} of a running container, or None."""
    if not container:
        return None
    try:
        r = subprocess.run(['docker', 'stats', '--no-stream', '--format', '{{.CPUPerc}}|{{.MemUsage}}|{{.NetIO}}', container],
                           capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    parts = r.stdout.strip().split('|')
    return dict(zip(('cpu', 'mem', 'net'), parts)) if r.returncode == 0 and len(parts) == 3 else None


def action_counts(log):
    """{'leituras','edições','buscas','comandos'} observed in a provider log."""
    counts = {'leituras': 0, 'edições': 0, 'buscas': 0, 'comandos': 0}
    for e in jsonl(log):
        item = e.get('item') or {}
        if e.get('type') == 'item.completed' and item.get('type') == 'command_execution':
            counts['comandos'] += 1
        elif e.get('type') == 'assistant' and isinstance(e.get('message'), dict):
            for block in e['message'].get('content') or []:
                if block.get('type') == 'tool_use':
                    key = {'Read': 'leituras', 'Edit': 'edições', 'Write': 'edições', 'Glob': 'buscas', 'Grep': 'buscas'}.get(block.get('name'))
                    if key:
                        counts[key] += 1
    return {k: v for k, v in counts.items() if v}


def task_progress(tasks, files):
    """[(task, touched, cited)] using the file names each plan task cites. A hint, not proof of completion."""
    names = [f[1] for f in files]
    out = []
    for t in tasks:
        cited = sorted(set(re.findall(r'[\w./-]+\.(?:astro|css|ts|tsx|js|json|md|html|yml|yaml|py)\b', t['description']))
                       | set(re.findall(r'(?:src|openspec)/[\w./-]*[\w]', t['description'])))
        touched = [c for c in cited if any(n == c or n.endswith('/' + c.split('/')[-1]) or n.startswith(c.rstrip('/') + '/') for n in names)]
        out.append((t, touched, cited))
    return out


def changes(path, state):
    """[(status, path, added, removed)] versus the base commit, read-only."""
    ws, base = str(path / 'workspace'), state['base_sha']
    rows = {}

    def git(*args):
        try:
            return subprocess.run(['git', '-C', ws, *args], capture_output=True, text=True, timeout=20).stdout
        except (OSError, subprocess.TimeoutExpired):
            return ''
    for line in git('diff', '--numstat', base).splitlines():
        a, r, name = (line.split('\t') + ['', '', ''])[:3]
        rows[name] = ('M', name, int(a) if a.isdigit() else 0, int(r) if r.isdigit() else 0)
    for name in git('ls-files', '--others', '--exclude-standard').splitlines():
        try:
            n = len((Path(ws) / name).read_text(errors='replace').splitlines())
        except OSError:
            n = 0
        rows[name] = ('A', name, n, 0)
    return sorted(rows.values(), key=lambda x: x[1])


def file_diff(path, state, name, limit=400):
    ws = str(path / 'workspace')
    tracked = subprocess.run(['git', '-C', ws, 'ls-files', '--error-unmatch', name], capture_output=True).returncode == 0
    cmd = ['git', '-C', ws, 'diff', state['base_sha'], '--', name] if tracked else \
        ['git', '-C', ws, 'diff', '--no-index', '--', '/dev/null', name]
    try:
        text = subprocess.run(cmd, capture_output=True, text=True, timeout=20).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ''
    lines = text.splitlines()
    return '\n'.join(lines[:limit]) + (f'\n… [{len(lines) - limit} linhas omitidas]' if len(lines) > limit else '')


def plan_view(state):
    plan = state.get('plan') or {}
    return plan.get('tasks', []), plan.get('acceptance_criteria', [])


def reviews(path, state):
    """{kind: result} from the latest cycle that has a result for that kind."""
    out = {}
    for kind in ('validate', 'review'):
        files = sorted(path.glob(f'*-{kind}.json'), key=lambda p: int(p.name.split('-')[0]))
        if files:
            try:
                out[kind] = json.loads(files[-1].read_text())
            except ValueError:
                pass
    return out


def verdicts(path, state):
    """{criterion id: (status, evidence)} merged over validate/review (FAIL wins)."""
    merged = {}
    for result in reviews(path, state).values():
        for r in result.get('acceptance_results', []):
            prev = merged.get(r['id'])
            if not prev or r['status'] == 'FAIL' or prev[0] == 'PASS' and r['status'] != 'PASS':
                merged[r['id']] = (r['status'], r.get('evidence', ''))
    return merged


def totals(path, state):
    t_in = t_out = 0
    cost = 0.0
    rows = []
    for run in state.get('stage_runs', []):
        log = path / f"{run_label(run)}.stdout"
        u = usage(log)
        t_in, t_out, cost = t_in + u['in'], t_out + u['out'], cost + (u['cost'] or 0)
        rows.append((run, u))
    return rows, t_in, t_out, cost


class Stall:
    """Tracks how long nothing observable moved (log size, changed files, container network)."""
    def __init__(self):
        self.sig, self.since = None, time.time()

    def idle(self, sig):
        if sig != self.sig:
            self.sig, self.since = sig, time.time()
        return time.time() - self.since


def signature(path, state, stats=None):
    stage = active_stage(state)
    log = stage_log(path, stage) if stage else None
    size = log.stat().st_size if log and log.exists() else 0
    return (size, len(changes(path, state)), (stats or {}).get('net', ''))


# ------------------------------------------------------------------ indicators

BAR_CHARS = '▏▎▍▌▋▊▉█'
SPARK = '▁▂▃▄▅▆▇█'


def bar(fraction, width=10):
    fraction = 0 if fraction is None else max(0.0, min(1.0, fraction))
    filled = round(fraction * width)
    return '▕' + '█' * filled + '░' * (width - filled) + '▏'


def spark(values):
    if not values:
        return ''
    top = max(values) or 1
    return ''.join(SPARK[min(len(SPARK) - 1, int(v / top * (len(SPARK) - 1) + 0.5))] if v else '▁' for v in values)


class Trend:
    """Activity per sample (log lines gained), sampled by the watch loop; the sparkline shows recent pace."""
    def __init__(self, size=24):
        self.size, self.last, self.deltas = size, None, []

    def push(self, count):
        if self.last is not None:
            self.deltas = (self.deltas + [max(0, count - self.last)])[-self.size:]
        self.last = count

    def line(self):
        return spark(self.deltas)


def log_lines(path, state):
    stage = active_stage(state)
    log = stage_log(path, stage) if stage else None
    try:
        return log.read_bytes().count(b'\n') if log else 0
    except OSError:
        return 0


def quota_snapshot(runs_dir, now=None):
    """Latest Claude subscription window utilization seen in any stage log (rate_limit_event), or None."""
    now = now or time.time()
    logs = sorted([p for kind in ('implement', 'review') for p in runs_dir.glob(f'*/*-{kind}.stdout')],
                  key=lambda p: p.stat().st_mtime, reverse=True)[:6]
    for log in logs:
        try:
            with log.open('rb') as fh:
                fh.seek(0, 2)
                fh.seek(max(0, fh.tell() - 600_000))
                tail = fh.read().decode(errors='replace').splitlines()
        except OSError:
            continue
        for line in reversed(tail):
            if '"rate_limit_event"' not in line:
                continue
            try:
                info = json.loads(line)['rate_limit_info']
            except (ValueError, KeyError):
                continue
            windows = info.get('unifiedWindows') or {}
            return {'status': info.get('status'), 'age': now - log.stat().st_mtime,
                    'five_hour': (windows.get('five_hour') or {}).get('utilization'),
                    'five_reset': (windows.get('five_hour') or {}).get('resetsAt'),
                    'seven_day': (windows.get('seven_day') or {}).get('utilization'),
                    'seven_reset': (windows.get('seven_day') or {}).get('resetsAt')}
    return None


def parse_limit(text):
    """('Codex'|'Claude', reset phrase) when a provider message says the plan/session limit is exhausted."""
    text = text or ''
    low = text.lower()
    provider = 'Codex' if ('usage limit' in low or 'chatgpt' in low) else 'Claude' if 'session limit' in low else None
    if not provider:
        return None
    m = re.search(r'(?:try again at|resets)\s+(.+?)\s*(?:\.\s*(?:;|$)|;|$)', text)
    return provider, (m.group(1).strip() if m else '?')


def limit_notice(runs_dir, now=None):
    """Most recent task stopped by an exhausted provider limit (last 24h): {'provider','reset','age'} or None."""
    now = now or time.time()
    for state_file in sorted(runs_dir.glob('*/state.json'), key=lambda p: p.stat().st_mtime, reverse=True)[:8]:
        age = now - state_file.stat().st_mtime
        if age > 86400:
            break
        try:
            found = parse_limit(json.loads(state_file.read_text()).get('reason'))
        except ValueError:
            continue
        if found:
            return {'provider': found[0], 'reset': found[1], 'age': age}
    return None


def stage_medians(runs_dir):
    """Median duration per stage from tasks that completed; falls back to any finished stage."""
    done, anyrun = {}, {}
    for state_file in runs_dir.glob('*/state.json'):
        try:
            st = json.loads(state_file.read_text())
        except ValueError:
            continue
        path = state_file.parent
        good = st.get('status') in ('REVIEWED', 'DELIVERED')
        samples = [(r['stage'], r.get('ended_at'), stage_started(path, r)) for r in st.get('stage_runs', [])]
        ev = st.get('test_evidence') or {}
        if ev.get('started_at') and ev.get('ended_at'):
            samples.append(('tests', ev['ended_at'], ev['started_at']))
        for stage, end, start in samples:
            if end and start and end > start:
                (done if good else anyrun).setdefault(stage, []).append(end - start)
    out = {}
    for stage in PIPELINE:
        values = sorted(done.get(stage) or anyrun.get(stage) or [])
        if values:
            out[stage] = values[len(values) // 2]
    return out


def progress(state, path, medians, now):
    """(fraction, eta_seconds|None) from stage statuses; the active stage counts by turns or its typical duration."""
    sts = steps(state, path)
    active = active_stage(state)
    total = len(PIPELINE)
    done = sum(1 for _, st, _ in sts if st == 'done')
    frac_active, eta = 0.0, 0.0
    known = True
    for name, status, seconds in sts:
        median = medians.get(name)
        if status == 'running':
            run = next((r for r in reversed(state.get('stage_runs', [])) if r['stage'] == name), None)
            elapsed = seconds or 0
            if run and run.get('max_turns'):
                log = stage_log(path, name)
                turns = session_profile(log)['turns'] if log else 0
                frac_active = min(0.95, turns / run['max_turns'])
                if run.get('parts', 1) > 1:  # sessions run one after another
                    frac_active = ((run.get('part', 1) - 1) + frac_active) / run['parts']
            elif median:
                frac_active = min(0.95, elapsed / median)
            if median:
                eta += max(median - elapsed, 0.1 * median)
            else:
                known = False
        elif status == 'pending':
            if median:
                eta += median
            else:
                known = False
    return (done + frac_active) / total, (eta if known else None)


def health(state, idle, quota, timeout_left_pct, turns, max_turns):
    """[(level, message)] where level is 1 (attention) or 2 (critical); empty list means OK."""
    out = []
    if state['status'] in ('FAILED', 'STOPPED', 'INTERRUPTED'):
        limit = parse_limit(state.get('reason'))
        out.append((2, f"limite de uso do {limit[0]} esgotado; volta em {limit[1]}" if limit
                    else f"tarefa {state['status']}: {short(state.get('reason') or '', 70)}"))
    if idle is not None and state['status'] == 'RUNNING':
        if idle > 600:
            out.append((2, f'sem movimento há {fmt_s(idle)}'))
        elif idle > 300:
            out.append((1, f'sem movimento há {fmt_s(idle)}'))
    if timeout_left_pct is not None:
        if timeout_left_pct < 10:
            out.append((2, 'timeout da etapa em < 10%'))
        elif timeout_left_pct < 25:
            out.append((1, 'timeout da etapa em < 25%'))
    if max_turns and turns:
        if turns >= 0.9 * max_turns:
            out.append((2, f'turnos {turns}/{max_turns}'))
        elif turns >= 0.75 * max_turns:
            out.append((1, f'turnos {turns}/{max_turns}'))
    if state.get('cycle', 0) >= 1 and state['status'] == 'RUNNING':
        out.append((1, f"ciclo de correção {state['cycle'] + 1}/{state['config']['max_cycles']}"))
    if quota:
        five = quota.get('five_hour')
        if quota.get('status') not in (None, 'allowed'):
            out.append((2, f"cota Claude: {quota['status']}"))
        elif five is not None and five >= 0.9:
            out.append((2, f'cota Claude 5h em {round(five * 100)}%'))
        elif five is not None and five >= 0.75:
            out.append((1, f'cota Claude 5h em {round(five * 100)}%'))
    return out


def _clock(epoch, now):
    if not epoch:
        return '?'
    t = time.localtime(epoch)
    return time.strftime('%H:%M' if epoch - now < 86400 else '%d/%m %H:%M', t)


def kpi_lines(path, state, idle, trend, quota, medians, now, width, limit=None):
    cfg = state['config']
    active = active_stage(state)
    run = next((r for r in reversed(state.get('stage_runs', [])) if r['stage'] == active), None) if active else None
    start = stage_started(path, run) if run else None
    timeout_left_pct = None
    if start:
        timeout_left_pct = 100 * max(0, cfg['timeout'] - (now - start)) / cfg['timeout']
    log = stage_log(path, active) if active else None
    sess = session_profile(log) if log else None
    turns = (sess['turns'] or sess['commands']) if sess else 0
    max_turns = run.get('max_turns') if run else None
    problems = health(state, idle, quota, timeout_left_pct, turns, max_turns)
    level = max((lv for lv, _ in problems), default=0)
    badge = {0: '● OK', 1: '● ATENÇÃO', 2: '● CRÍTICO'}[level]
    lines = [f"SAÚDE      {badge}" + ('  ' + ' · '.join(m for _, m in problems) if problems else '  tudo dentro dos limites')]
    frac, eta = progress(state, path, medians, now)
    terminal = state['status'] in TERMINAL
    lines.append(f"PROGRESSO  {bar(frac, 20)} {round(frac * 100)}%" + ('' if terminal else
                 (f"  ·  faltam ~{fmt_s(eta)}" if eta is not None else '  ·  ETA indisponível (sem histórico)')))
    if quota:
        five, seven = quota.get('five_hour'), quota.get('seven_day')
        fresh = f"lido há {fmt_s(quota['age'])}"
        lines.append(f"COTA CLAUDE  5h {bar(five)} {round((five or 0) * 100)}% (reseta {_clock(quota.get('five_reset'), now)})"
                     f"  ·  7d {bar(seven)} {round((seven or 0) * 100)}% (reseta {_clock(quota.get('seven_reset'), now)})  ·  {fresh}")
    else:
        lines.append('COTA CLAUDE  sem leitura ainda (aparece após a primeira etapa Claude)')
    if limit:
        lines.append(f"LIMITE     ⚠ {limit['provider']} esgotado — volta em {limit['reset']} (falha há {fmt_s(limit['age'])})")
    if active and sess:
        shape, clock = [], []
        if run and run.get('parts', 1) > 1:
            shape.append(f"sessão {run['part']}/{run['parts']}")
        if max_turns:
            shape.append(f"turnos {turns}/{max_turns} {bar(turns / max_turns, 8)}")
        elif turns:
            shape.append(f"comandos {turns}")
        if sess['ctx_last']:
            shape.append(f"contexto {sess['ctx_last'] // 1000}k (pico {sess['ctx_peak'] // 1000}k)")
        if sess['thinking']:
            shape.append(f"raciocínio ~{sess['thinking'] // 1000}k")
        if timeout_left_pct is not None:
            clock.append(f"timeout {bar(1 - timeout_left_pct / 100, 8)} {fmt_s(max(0, cfg['timeout'] - (now - start)))} restantes")
        pace = trend.line() if trend else ''
        if pace:
            clock.append(f'ritmo {pace}')
        lines.append('ETAPA ATUAL  ' + '  ·  '.join(shape))
        if clock:
            lines.append('             ' + '  ·  '.join(clock))
    rows, t_in, t_out, cost = totals(path, state)
    spent = f'US$ {cost:.2f} (Claude)' if cost else 'custo Claude ao fim da etapa'
    elapsed_min = max((now - state['created_at']) / 60, 1 / 60)
    lines.append(f"CONSUMO    tokens {t_in:,} in / {t_out:,} out  ·  {spent}  ·  {t_in / elapsed_min / 1000:.0f}k tokens/min")
    return lines


# ------------------------------------------------------------------ text view

def _fit(lines, width):
    return [x if len(x) < width else x[:width - 1] + '…' for x in lines]


def render_text(path, state, idle=None, now=None, stats=None, width=110, height=None, trend=None, quota=None, medians=None, limit=None):
    """Terminal view. With `height`, drops detail level by level so the header never scrolls away."""
    now = now or time.time()
    if state['status'] in TERMINAL or state['status'] == 'COMPLETE':  # finished: freeze elapsed time at the end
        try:
            now = min(now, (path / 'state.json').stat().st_mtime)
        except OSError:
            pass
    for level in range(4):
        lines = _text_lines(path, state, idle, now, stats, width, level, trend, quota, medians or {}, limit)
        if height is None or len(lines) <= height - 3:
            break
    if height is not None and len(lines) > height - 3:
        lines = lines[:height - 4] + ['… (aumente a janela para ver mais)']
    return '\n'.join(_fit(lines, width))


def _text_lines(path, state, idle, now, stats, width, level, trend=None, quota=None, medians=None, limit=None):
    cfg = state['config']
    plan = state.get('plan') or {}
    rows, t_in, t_out, cost = totals(path, state)
    worker = state.get('worker') or {}
    head = (state.get('head_sha') or '')[:8]
    lines = [f"Tarefa {state['task'][:8]} · {state['status']} · ciclo {state['cycle'] + 1}/{cfg['max_cycles']}"
             f" · decorrido {fmt_s(now - state['created_at'])} de {fmt_s(cfg['max_seconds'])}"
             + (f" · risco {plan['risk']}" if plan.get('risk') else '') + (f' · HEAD {head}' if head else ''),
             f"Projeto: {state['repository']} · base {state['base_sha'][:8]}",
             'Pedido: ' + short(state['request'], width)]
    lines += [''] + kpi_lines(path, state, idle, trend, quota, medians or {}, now, width, limit)
    # --- stages
    lines += ['', 'ETAPAS']
    for name, status, seconds in steps(state, path):
        label, info = STAGE_INFO[name]
        model = next((f"{r['requested_model']} ({r['effort']})" for r in reversed(state.get('stage_runs', [])) if r['stage'] == name), '')
        lines.append(f" {ICON[status]} {label:<22} {fmt_s(seconds) if seconds is not None else '':>7}  {model}")
    active = active_stage(state)
    if active:
        run = next((r for r in reversed(state['stage_runs']) if r['stage'] == active), None)
        start = stage_started(path, run) if run else None
        lines += ['', f'AGORA: {STAGE_INFO[active][0]} — {STAGE_INFO[active][1]}']
        if start:
            left = min(cfg['timeout'] - (now - start), cfg['max_seconds'] - (now - state['created_at']))
            lines.append(f"   na etapa há {fmt_s(now - start)} · timeout da etapa em {fmt_s(left)}")
        if stats:
            lines.append(f"   container: CPU {stats['cpu']} · memória {stats['mem']} · rede {stats['net']}")
        log = stage_log(path, active)
        counts = action_counts(log) if log else {}
        if counts:
            lines.append('   ações até agora: ' + ' · '.join(f'{v} {k}' for k, v in counts.items()))
        if worker:
            lines.append(f"   worker pid {worker.get('pid')} · container {(state.get('active') or {}).get('container', '')[-24:]}")
        if idle is not None:
            lines.append(f"   último movimento observável há {fmt_s(idle)}" + ('  ⚠ possível travamento' if idle > 300 else ''))
        prompt = stage_prompt(path, state, active)
        if prompt and level <= 2:
            instruction, _ = prompt_view(prompt, state['request'])
            lines.append(f"   PROMPT em execução ({len(prompt):,} caracteres):")
            lines += ['     ' + x for x in wrap(instruction, width - 8, (8, 4, 2)[level])]
            sent = handoff_files(path, active, run['cycle'], run_label(run)) if run else []
            if sent and level == 0:
                lines.append('     arquivos entregues: ' + ', '.join(f'{n} ({sz:,} B)' for n, sz in sent))
            items = feedback_items(state)
            if items and level <= 1:
                lines.append(f'     feedback a tratar neste ciclo ({len(items)}):')
                lines += ['       • ' + short(x, width - 12) for x in items[:(5 if level == 0 else 2)]]
    # --- plan
    tasks, criteria = plan_view(state)
    verdict = verdicts(path, state)
    files = changes(path, state)
    if tasks:
        progress = task_progress(tasks, files)
        lines += ['', f'PLANO · {len(tasks)} tarefas · {len(criteria)} critérios'
                  + (f" · fora de escopo: {short('; '.join(plan.get('out_of_scope', [])), 60)}" if level == 0 and plan.get('out_of_scope') else '')]
        if level <= 1:
            for t, touched, cited in progress:
                mark = '·' if not cited else '●' if len(touched) == len(cited) else '◐' if touched else '○'
                lines.append(f"   {mark} {t['id']} {short(t['description'], width - 24)}" + (f' [{len(touched)}/{len(cited)} arq.]' if cited else ''))
            lines.append('   (● todos / ◐ alguns / ○ nenhum dos arquivos citados na tarefa foi alterado; indício, não verificação)')
        else:
            done = sum(1 for _, t, c in progress if c and len(t) == len(c))
            lines.append(f'   tarefas com todos os arquivos citados alterados: {done}/{len(tasks)}')
        if level == 0:
            for c in criteria:
                mark = {'PASS': '✔', 'FAIL': '✖', 'INCONCLUSIVE': '?'}.get(verdict.get(c['id'], ('',))[0], '·')
                lines.append(f"   {mark} {c['id']} {short(c['description'], width - 12)}")
        else:
            counts = {k: sum(1 for v in verdict.values() if v[0] == k) for k in ('PASS', 'FAIL', 'INCONCLUSIVE')}
            lines.append(f"   critérios: ✔ {counts['PASS']} · ✖ {counts['FAIL']} · ? {counts['INCONCLUSIVE']} · "
                         f"aguardando {len(criteria) - sum(counts.values())}")
    # --- files
    if files:
        limit = (15, 8, 5, 3)[level]
        added, removed = sum(f[2] for f in files), sum(f[3] for f in files)
        lines += ['', f'ARQUIVOS ALTERADOS · {len(files)} · +{added} −{removed}']
        for s, n, a, r in sorted(files, key=lambda f: -(f[2] + f[3]))[:limit]:
            lines.append(f"   {s} {short(n, width - 22):<{min(width - 22, 60)}} +{a} −{r}")
        if len(files) > limit:
            lines.append(f'   … e mais {len(files) - limit}')
    # --- tests / reviews
    ev = state.get('test_evidence')
    if ev:
        took = f" em {fmt_s(ev['ended_at'] - ev['started_at'])}" if ev.get('started_at') and ev.get('ended_at') else ''
        lines += ['', f"TESTES: {'OK' if not ev['exit_code'] else 'FALHOU (exit ' + str(ev['exit_code']) + ')'}{took} · "
                  + ' ; '.join(short(c, 40) for c in ev['checks'])]
        if ev['exit_code'] and level <= 1:
            lines += ['   ' + short(x, width - 4) for x in ev.get('output', '').splitlines()[-5:]]
    for kind, result in reviews(path, state).items():
        open_ = [f for f in result.get('findings', []) if f['status'] == 'OPEN']
        lines.append(f"{kind.upper()}: {result['verdict']} · {len(open_)} achado(s) aberto(s)"
                     + (' · ' + ', '.join(f"{f['severity']}" for f in open_) if open_ else ''))
        if level == 0:
            lines += ['   ' + short(f"{f['severity']} {f['summary']}", width - 4) for f in open_[:5]]
    # --- activity
    stage, recent = feed(path, state, n=(10, 6, 4, 3)[level])
    if recent:
        lines += ['', f'ATIVIDADE RECENTE · {STAGE_INFO[stage][0]}'] + ['   ' + x for x in recent]
    # --- consumption
    lines += ['', 'CONSUMO POR ETAPA']
    for run, u in rows:
        start = stage_started(path, run)
        dur = f" · {fmt_s((run.get('ended_at') or (now if active == run['stage'] else start or now)) - start)}" if start else ''
        usage_txt = f"tokens in {u['in']:,} / out {u['out']:,}" if u['events'] else 'tokens ao fim da etapa'
        lines.append(f"   {run['agent']:<8}{run['stage']:<10}{usage_txt}" + (f" · US$ {u['cost']:.2f}" if u['cost'] is not None else '') + dur)
    lines.append(f"   total: tokens in {t_in:,} / out {t_out:,}" + (f' · US$ {cost:.2f}' if cost else ''))
    if state.get('reason'):
        lines.append('Motivo: ' + str(state['reason']))
    lines.append('Logs: ' + str(path) + '   (ai-team serve para o painel web)')
    return lines


# ------------------------------------------------------------------ efficiency

def _marked_len(text):
    """Original size of a string that slim() shortened ('… [N chars]'), else its length."""
    m = re.search(r'… \[(\d+) chars\]$', text)
    return int(m.group(1)) if m else len(text)


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for x in value:
            yield from _strings(x)
    elif isinstance(value, dict):
        for x in value.values():
            yield from _strings(x)


def tool_profile(log):
    """What the agent pulled into its context. `identical` counts the same read repeated verbatim (real waste);
    `windows` counts files read in several different ranges (chunked reading, not waste by itself)."""
    out_bytes, per_command, identical, windows = 0, {}, {}, {}
    for e in jsonl(log):
        item = e.get('item') or {}
        if e.get('type') == 'item.completed' and item.get('type') == 'command_execution':  # codex
            size = len(item.get('aggregated_output') or '')
            raw = re.sub(r"^/bin/(ba)?sh -lc ", '', item.get('command', '')).strip('\'" ')
            words = raw.split()
            name = words[0] if words else '?'
            if name == 'rtk' and len(words) > 1:
                name = 'rtk ' + words[1]
            per_command[name] = per_command.get(name, 0) + size
            out_bytes += size
            if words and words[0] in ('cat', 'sed', 'nl', 'head', 'tail', 'rg', 'grep', 'git'):
                identical[raw] = identical.get(raw, 0) + 1
            if words and words[0] in ('sed', 'nl', 'head', 'tail'):
                target = next((w for w in reversed(words) if re.search(r'\.\w{1,5}$', w)), None)
                if target:
                    windows.setdefault(target, set()).add(raw)
        elif e.get('type') == 'user':  # claude tool results
            out_bytes += sum(_marked_len(x) for x in _strings((e.get('message') or {}).get('content')))
        elif e.get('type') == 'assistant' and isinstance(e.get('message'), dict):
            for block in e['message'].get('content') or []:
                if block.get('type') == 'tool_use' and block.get('name') == 'Read':
                    i = block.get('input') or {}
                    key = f"{i.get('file_path', '')}@{i.get('offset')}:{i.get('limit')}"
                    identical[key] = identical.get(key, 0) + 1
                    windows.setdefault(i.get('file_path', ''), set()).add(key)
    top = sorted(per_command.items(), key=lambda x: -x[1])[:3]
    return {'bytes': out_bytes, 'top': top,
            'identical': sorted(((k, n) for k, n in identical.items() if n > 1), key=lambda x: -x[1])[:3],
            'windows': sorted(((f, len(v)) for f, v in windows.items() if len(v) >= 3), key=lambda x: -x[1])[:3]}


def session_profile(log):
    """Turn-level shape of a session: turns, context growth, thinking, parallel calls. Works for Claude streams;
    for Codex only the command count is meaningful."""
    msgs, thinking, calls_per_turn, commands = {}, 0, {}, 0
    for e in jsonl(log):
        if e.get('type') == 'assistant' and isinstance(e.get('message'), dict):
            m = e['message']
            key = m.get('id') or len(msgs)
            msgs[key] = m.get('usage') or {}
            calls_per_turn[key] = calls_per_turn.get(key, 0) + sum(1 for b in m.get('content') or [] if b.get('type') == 'tool_use')
        elif e.get('type') == 'system' and e.get('subtype') == 'thinking_tokens':
            thinking += e.get('estimated_tokens_delta', 0)
        elif e.get('type') == 'item.completed' and (e.get('item') or {}).get('type') == 'command_execution':
            commands += 1
    ctx = [sum(u.get(k, 0) for k in ('input_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens')) for u in msgs.values()]
    tool_turns = [n for n in calls_per_turn.values() if n]
    return {'turns': len(ctx), 'commands': commands, 'ctx_last': ctx[-1] if ctx else 0, 'ctx_peak': max(ctx, default=0),
            'ctx_sum': sum(ctx), 'thinking': thinking,
            'parallel_pct': round(100 * sum(1 for n in tool_turns if n > 1) / len(tool_turns)) if tool_turns else None}


def host_tools():
    """Token-saving tools on this host and whether the stages use them."""
    info = {}
    for name in ('rtk', 'headroom'):
        try:
            r = subprocess.run([name, '--version'], capture_output=True, text=True, timeout=10)
            info[name] = r.stdout.strip().splitlines()[0] if r.returncode == 0 and r.stdout.strip() else None
        except (OSError, subprocess.TimeoutExpired):
            info[name] = None
    return info


def efficiency(path, state):
    rows = []
    for run in state.get('stage_runs', []):
        log = path / f"{run_label(run)}.stdout"
        u = usage(log)
        prof = tool_profile(log)
        sess = session_profile(log)
        rows.append({'cycle': run['cycle'], 'stage': run['stage'], 'part': run.get('part', 1), 'parts': run.get('parts', 1), 'agent': run['agent'], 'provider': run.get('provider', ''),
                     'in': u['in'], 'out': u['out'], 'cached': u['cached'], 'cost': u['cost'],
                     'cache_pct': round(100 * u['cached'] / u['in']) if u['in'] else None,
                     'tool_bytes': prof['bytes'], 'top': prof['top'], 'identical': prof['identical'], 'windows': prof['windows'],
                     'turns': sess['turns'], 'commands': sess['commands'], 'ctx_peak': sess['ctx_peak'], 'ctx_sum': sess['ctx_sum'],
                     'thinking': sess['thinking'], 'parallel_pct': sess['parallel_pct'], 'max_turns': run.get('max_turns'),
                     'rtk': (run.get('tools') or {}).get('rtk'),
                     'seconds': (run.get('ended_at') or time.time()) - (stage_started(path, run) or time.time())})
    return rows


def row_tag(r):
    return f"{r['cycle'] + 1}/{r['stage']}" + (f"#{r['part']}" if r.get('parts', 1) > 1 else '')


def recommendations(rows):
    """Rule-based hints, each carrying the number that justifies it. Empty list means nothing evident to fix."""
    out = []
    for r in rows:
        tag = row_tag(r)
        if r['provider'] == 'claude' and r['turns'] >= 20 and r['ctx_sum'] >= 1_000_000:
            out.append(f"{tag}: sessão longa — {r['turns']} turnos relendo até {r['ctx_peak'] // 1000}k tokens "
                       f"(soma de contexto relido {r['ctx_sum'] / 1e6:.1f}M). O custo cresce de forma quase quadrática com os turnos; "
                       'dividir o trabalho em sessões menores é uma hipótese a validar (não aplicada).')
        if r['out'] and r['thinking'] and r['thinking'] / r['out'] >= 0.5 and r['thinking'] >= 10_000:
            out.append(f"{tag}: raciocínio estimado ≈ {round(100 * r['thinking'] / r['out'])}% da saída ({r['thinking'] // 1000}k tokens); "
                       'avaliar effort menor nesta etapa é um trade-off de qualidade, decisão do operador.')
        if r['provider'] == 'codex' and r['commands'] >= 20:
            out.append(f"{tag}: {r['commands']} comandos = {r['commands']} turnos relendo o contexto; "
                       'agrupar leituras (cat a b c) reduz turnos.')
        if r['identical']:
            f, n = r['identical'][0]
            out.append(f"{tag}: leitura idêntica repetida {n}× ({f.split('/')[-1][:60]}) — desperdício direto.")
        if r['max_turns'] and r['turns'] >= 0.8 * r['max_turns']:
            out.append(f"{tag}: {r['turns']}/{r['max_turns']} turnos — perto do limite; risco de falha por orçamento.")
        if r['cache_pct'] is not None and r['in'] > 100_000 and r['cache_pct'] < 60:
            out.append(f"{tag}: cache de apenas {r['cache_pct']}% — prefixo do prompt instável ou sessões curtas demais.")
    return out


def render_efficiency(path, state):
    rows = efficiency(path, state)
    tools = host_tools()
    lines = [f"EFICIÊNCIA DE TOKENS · tarefa {state['task'][:8]} · {state['status']}", '',
             f"{'CICLO/ETAPA':<14}{'AGENTE':<8}{'TOKENS IN/OUT':>22}{'CACHE':>7}{'CUSTO':>9}{'TURNOS':>8}{'CTX PICO':>10}{'PARAL.':>8}{'SAÍDA FERR.':>13}  RTK"]
    for r in rows:
        turns = r['turns'] or r['commands']
        lines.append(f"{row_tag(r):<14}{r['agent']:<8}{r['in']:>13,}/{r['out']:<8,}"
                     f"{(str(r['cache_pct']) + '%') if r['cache_pct'] is not None else '—':>7}"
                     f"{('%.2f' % r['cost']) if r['cost'] is not None else '—':>9}{turns:>8}"
                     f"{(str(r['ctx_peak'] // 1000) + 'k') if r['ctx_peak'] else '—':>10}"
                     f"{(str(r['parallel_pct']) + '%') if r['parallel_pct'] is not None else '—':>8}{r['tool_bytes'] / 1024:>10.0f} KB  "
                     + (f"aplicado ({r['rtk']})" if r['rtk'] else ('n/a (sem shell)' if r['provider'] == 'claude' else 'não aplicado')))
    hot = [r for r in rows if r['top'] or r['windows']]
    if hot:
        lines += ['', 'ONDE ESTÃO OS TOKENS']
        for r in hot:
            parts = []
            if r['top']:
                parts.append('maiores saídas: ' + ', '.join(f'{n} {b / 1024:.0f} KB' for n, b in r['top']))
            if r['windows']:
                parts.append('lido em várias janelas: ' + ', '.join(f'{f.split("/")[-1]} ×{n}' for f, n in r['windows']))
            lines.append(f"   {row_tag(r)}: " + ' · '.join(parts))
    recs = recommendations(rows)
    lines += ['', 'RECOMENDAÇÕES (baseadas nos números acima)'] + (['   • ' + x for x in recs] if recs else ['   nenhum desperdício evidente'])
    lines += ['', 'FERRAMENTAS DO HOST']
    lines.append(f"   rtk: {tools['rtk'] or 'não instalado'} · aplicado aos estágios Codex (binário somente leitura, telemetria off); "
                 'não se aplica ao Claude, que roda sem Bash')
    lines.append(f"   headroom: {tools['headroom'] or 'não instalado'} · NÃO roteado para os estágios (ver openspec/changes/token-efficiency-parity)")
    return '\n'.join(lines)


# ------------------------------------------------------------------ html view

CSS = """:root{--bg:#fff;--fg:#1d2330;--mut:#5b6475;--card:#f4f6fa;--ok:#157f3c;--bad:#b42318;--run:#1a56db;--bd:#d8dde7}
@media(prefers-color-scheme:dark){:root{--bg:#10141c;--fg:#e6e9f0;--mut:#9aa3b5;--card:#1a2030;--ok:#4cc27a;--bad:#ff7b72;--run:#6ea8ff;--bd:#2b3347}}
body{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;margin:0;padding:16px;max-width:1000px;margin-inline:auto}
h1{font-size:20px;margin:0 0 4px}h2{font-size:16px;margin:24px 0 8px;border-bottom:1px solid var(--bd);padding-bottom:4px}
.mut{color:var(--mut)}.card{background:var(--card);border:1px solid var(--bd);border-radius:8px;padding:10px 12px;margin:6px 0}
.done{color:var(--ok)}.failed{color:var(--bad)}.running{color:var(--run);font-weight:600}.pending{color:var(--mut)}
table{border-collapse:collapse;width:100%}td,th{padding:4px 8px;border-bottom:1px solid var(--bd);text-align:left;vertical-align:top}
pre{background:var(--card);padding:8px;overflow:auto;font-size:12px;border-radius:6px;max-height:420px}
.add{color:var(--ok)}.del{color:var(--bad)}a{color:var(--run)}"""


def e(value):
    return html.escape(str(value))


def render_html(path, state, live=False, now=None):
    now = now or time.time()
    cfg = state['config']
    rows, t_in, t_out, cost = totals(path, state)
    out = [f"<h1>Tarefa {e(state['task'][:8])} · <span class='{'done' if state['status'] in ('REVIEWED', 'DELIVERED') else 'failed' if state['status'] in ('FAILED', 'STOPPED', 'INTERRUPTED') else 'running'}'>{e(state['status'])}</span></h1>",
           f"<div class='mut'>Projeto: {e(state['repository'])} · base {e(state['base_sha'][:8])} · ciclo {state['cycle'] + 1}/{cfg['max_cycles']} · "
           f"decorrido {fmt_s(now - state['created_at'])}</div>", f"<div class='card'><b>Pedido:</b> {e(state['request'])}</div>"]
    if state.get('reason'):
        out.append(f"<div class='card failed'><b>Motivo da parada:</b> {e(state['reason'])}</div>")
    out.append('<h2>Etapas</h2><table><tr><th></th><th>Etapa</th><th>Duração</th><th>O que faz</th></tr>')
    for name, status, seconds in steps(state, path):
        label, info = STAGE_INFO[name]
        out.append(f"<tr class='{status}'><td>{ICON[status]}</td><td>{e(label)}</td><td>{e(fmt_s(seconds)) if seconds is not None else ''}</td><td class='mut'>{e(info)}</td></tr>")
    out.append('</table>')
    prompts = []
    for run in state.get('stage_runs', []):
        text = stage_prompt(path, state, run['stage'], run['cycle'], run_label(run))
        if text:
            prompts.append(f"<details><summary>Ciclo {run['cycle'] + 1} · {e(STAGE_INFO[run['stage']][0])}{' · sessão ' + str(run['part']) + '/' + str(run['parts']) if run.get('parts', 1) > 1 else ''} · {len(text):,} caracteres</summary><pre>{e(text)}</pre></details>")
    if prompts:
        out.append('<h2>Prompts enviados aos agentes</h2>' + ''.join(prompts))
    stage, recent = feed(path, state, n=12)
    if recent:
        out.append(f"<h2>Atividade recente · {e(STAGE_INFO[stage][0])}</h2><pre>{e(chr(10).join(recent))}</pre>")
    tasks, criteria = plan_view(state)
    verdict = verdicts(path, state)
    if tasks:
        out.append('<h2>Plano</h2><table><tr><th>Tarefa</th><th>Descrição</th><th>Critérios</th></tr>')
        out += [f"<tr><td>{e(t['id'])}</td><td>{e(t['description'])}</td><td>{e(', '.join(t['acceptance_ids']))}</td></tr>" for t in tasks]
        out.append('</table><h2>Critérios de aceite</h2><table><tr><th></th><th>ID</th><th>Critério</th><th>Veredito / evidência</th></tr>')
        for c in criteria:
            st, ev = verdict.get(c['id'], ('', ''))
            cls = {'PASS': 'done', 'FAIL': 'failed'}.get(st, 'pending')
            out.append(f"<tr><td class='{cls}'>{ {'PASS': '✔', 'FAIL': '✖', 'INCONCLUSIVE': '?'}.get(st, '·') }</td><td>{e(c['id'])}</td>"
                       f"<td>{e(c['description'])}</td><td class='mut'>{e(st)} {e(ev)}</td></tr>")
        out.append('</table>')
    files = changes(path, state)
    if files:
        out.append(f"<h2>Arquivos alterados ({len(files)}) · <span class='add'>+{sum(f[2] for f in files)}</span> <span class='del'>−{sum(f[3] for f in files)}</span></h2>")
        for s, name, a, r in files:
            body = '' if live else f"<pre>{e(file_diff(path, state, name))}</pre>"
            out.append(f"<details><summary>{e(s)} {e(name)} <span class='add'>+{a}</span> <span class='del'>−{r}</span></summary>{body}</details>")
    ev = state.get('test_evidence')
    if ev:
        out.append(f"<h2>Testes</h2><div class='card {'done' if not ev['exit_code'] else 'failed'}'>"
                   f"{'OK' if not ev['exit_code'] else 'FALHOU'} (exit {e(ev['exit_code'])}) · {e(' ; '.join(ev['checks']))}</div>"
                   f"<details><summary>Saída (final)</summary><pre>{e(ev.get('output', ''))}</pre></details>")
    for kind, result in reviews(path, state).items():
        out.append(f"<h2>{e(STAGE_INFO[kind][0])} · {e(result['verdict'])}</h2>")
        for f in result.get('findings', []):
            out.append(f"<div class='card'><b>{e(f['severity'])}</b> · {e(f['status'])} · {e(f['summary'])}</div>")
        if result.get('residual_risks'):
            out.append('<div class="mut">Riscos residuais: ' + e('; '.join(map(str, result['residual_risks']))) + '</div>')
    eff = efficiency(path, state)
    if eff:
        out.append('<h2>Eficiência de tokens</h2><table><tr><th>Etapa</th><th>Cache</th><th>Turnos</th><th>Ctx pico</th><th>Saída de ferramentas</th><th>Maiores saídas</th><th>RTK</th></tr>')
        for r in eff:
            out.append(f"<tr><td>{r['cycle'] + 1}/{e(r['stage'])}</td><td>{'' if r['cache_pct'] is None else str(r['cache_pct']) + '%'}</td>"
                       f"<td>{r['turns'] or r['commands']}</td><td>{r['ctx_peak'] // 1000}k</td><td>{r['tool_bytes'] / 1024:.0f} KB</td><td>{e(', '.join(f'{n} {b / 1024:.0f} KB' for n, b in r['top']))}</td>"
                       f"<td>{e(r['rtk'] or ('n/a' if r['provider'] == 'claude' else 'não aplicado'))}</td></tr>")
        out.append('</table>')
    out.append('<h2>Consumo</h2><table><tr><th>Agente</th><th>Etapa</th><th>Modelo</th><th>Tokens in</th><th>Tokens out</th><th>Custo</th></tr>')
    for run, u in rows:
        out.append(f"<tr><td>{e(run['agent'])}</td><td>{e(run['stage'])}</td><td>{e(run['requested_model'])} ({e(run['effort'])})</td>"
                   f"<td>{u['in']:,}</td><td>{u['out']:,}</td><td>{'US$ %.2f' % u['cost'] if u['cost'] is not None else '—'}</td></tr>")
    out.append(f"<tr><th colspan=3>Total</th><th>{t_in:,}</th><th>{t_out:,}</th><th>{'US$ %.2f' % cost if cost else ''}</th></tr></table>")
    refresh = "<meta http-equiv='refresh' content='5'>" if live and state['status'] == 'RUNNING' else ''
    return (f"<!doctype html><html lang='pt-BR'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"{refresh}<title>ai-team {e(state['task'][:8])}</title><style>{CSS}</style><body>" + ''.join(out)
            + "<p class='mut'>Somente leitura. Conteúdo gerado por agentes é exibido como texto, nunca executado.</p></body></html>")


# ------------------------------------------------------------------ history

def history_rows(runs_dir, now=None):
    now = now or time.time()
    rows = []
    for state_file in sorted(runs_dir.glob('*/state.json'), key=lambda p: p.stat().st_mtime):
        try:
            state = json.loads(state_file.read_text())
        except ValueError:
            continue
        path = state_file.parent
        end = state_file.stat().st_mtime if state['status'] in TERMINAL else now
        _, t_in, t_out, cost = totals(path, state)
        rows.append({'id': state['task'], 'status': state['status'], 'cycles': state['cycle'] + 1,
                     'seconds': end - state['created_at'], 'tokens_in': t_in, 'tokens_out': t_out, 'cost': cost,
                     'files': len(changes(path, state)) if (path / 'workspace').exists() else 0,
                     'request': state['request']})
    return rows


def render_history(rows):
    lines = [f"{'ID':<9}{'STATUS':<10}{'CICLOS':>6}{'DURAÇÃO':>9}{'TOKENS IN/OUT':>22}{'CUSTO':>9}{'ARQ':>5}  PEDIDO"]
    for r in rows:
        lines.append(f"{r['id'][:8]:<9}{r['status']:<10}{r['cycles']:>6}{fmt_s(r['seconds']):>9}"
                     f"{r['tokens_in']:>13,}/{r['tokens_out']:<8,}{('%.2f' % r['cost']) if r['cost'] else '—':>9}{r['files']:>5}  {short(r['request'], 50)}")
    return '\n'.join(lines)
