#!/usr/bin/env python3
"""Check paths, distribution identities and literal native imports (Python 3.11+).

Static guard, not a sandbox or a resolver for arbitrary generated imports.
Documentation and evidence fixtures are not runtime dependencies.
"""
import ast
import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODE = {'.py', '.ts', '.tsx', '.js', '.jsx', '.cjs', '.mjs', '.sh', '.toml', '.yaml', '.yml', '.json'}
SKIP = {'node_modules', 'dist', 'build', '.git', '__pycache__', '.venv', '.pytest_cache', 'fixtures', 'artifacts', 'validation'}


def normalized(name):
    return re.sub(r'[-_.]+', '-', name).lower()


def package_files(path):
    return [p for p in path.rglob('*') if p.is_file() and not SKIP.intersection(p.relative_to(path).parts)]


def identities(packages, root):
    result = {}
    for name, spec in packages.items():
        names = {f'product-platform-{name}', f'@leandroclf/product-platform-{name}', *spec.get('distributions', [])}
        for file in package_files(root / spec['path']):
            if file.name == 'package.json':
                value = json.loads(file.read_text()).get('name')
            elif file.name == 'pyproject.toml':
                value = tomllib.loads(file.read_text()).get('project', {}).get('name')
            else:
                continue
            if value:
                names.add(value)
        result[name] = {'names': names, 'python': set(spec.get('python_modules', []))}
    return result


def imports(file, text):
    if file.suffix == '.py':
        tree = ast.parse(text, filename=str(file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                yield from (alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                yield node.module
    elif file.suffix in {'.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs'}:
        pattern = r'''(?:^\s*(?:import|export)\s+(?:[^;\n]*?\s+from\s+)?|\b(?:require|import)\s*\(\s*)["']([^"']+)["']'''
        yield from re.findall(pattern, text, re.M)


def dependencies(file, text):
    if file.name == 'package.json':
        data = json.loads(text)
        for key in ('dependencies', 'devDependencies', 'peerDependencies', 'optionalDependencies'):
            yield from data.get(key, {})
    elif file.name == 'pyproject.toml':
        project = tomllib.loads(text).get('project', {})
        requirements = list(project.get('dependencies', []))
        for values in project.get('optional-dependencies', {}).values():
            requirements.extend(values)
        for value in requirements:
            match = re.match(r'\s*([A-Za-z0-9_.-]+)', value)
            if match:
                yield match.group(1)
    elif file.name.startswith('requirements') and file.suffix == '.txt':
        for line in text.splitlines():
            match = re.match(r'\s*([A-Za-z0-9_.-]+)(?:\s|[<>=!~;\[@]|$)', line)
            if match:
                yield match.group(1)


def violations(config: dict, root: Path = ROOT) -> list[str]:
    packages = config['packages']
    found = []
    known = identities(packages, root)
    for name, spec in packages.items():
        allowed = {name, *spec['depends_on']}
        others = [q for q in packages if q not in allowed]
        if name in spec['depends_on'] or not set(spec['depends_on']) <= set(packages):
            found.append(f'platform-packages.json: {name} tem dependência inválida')
        for file in package_files(root / spec['path']):
            if file.suffix not in CODE and not file.name.startswith('requirements'):
                continue
            text = file.read_text(errors='strict')
            rel = file.relative_to(root)
            deps, modules = list(dependencies(file, text)), list(imports(file, text))
            for other in others:
                if re.search(rf'packages/{re.escape(other)}/|\.\./+{re.escape(other)}/', text):
                    found.append(f'{rel}: {name} referencia o caminho do pacote {other}')
                names = known[other]['names']
                if any(normalized(dep) in {normalized(n) for n in names} for dep in deps):
                    found.append(f'{rel}: dependência de {name} aponta para o pacote {other}')
                if any(module in names or any(module == n or module.startswith(n + '.') for n in known[other]['python'])
                       or any(module.startswith(n + '/') for n in names) for module in modules):
                    found.append(f'{rel}: import de {name} aponta para o pacote {other}')
    visiting, done = set(), set()

    def visit(name):
        if name in visiting:
            found.append(f'platform-packages.json: ciclo de dependências em {name}')
            return
        if name in done:
            return
        visiting.add(name)
        for dep in packages[name]['depends_on']:
            if dep in packages and dep != name:
                visit(dep)
        visiting.remove(name)
        done.add(name)

    for name in packages:
        visit(name)
    return found


if __name__ == '__main__':
    problems = violations(json.loads((ROOT / 'platform-packages.json').read_text()))
    for line in problems:
        print('VIOLAÇÃO ' + line, file=sys.stderr)
    print('Fronteiras entre pacotes: ' + ('VIOLADAS' if problems else 'OK'))
    sys.exit(1 if problems else 0)
