# Auditoria de dependências e Python 3.10

Correção proposta para #127. O runtime continua suportando Python >=3.10 e a matriz continua executando testes, lint, tipos, verificação de dependências e build em 3.10/3.11/3.12.

`pip-audit` depende de `CacheControl[filecache]`, que depende de `filelock`. O CI3.10 resolveu filelock4.1.0 e a auditoria falhou. A versão corrigida4.2.1 exige Python>=3.11 ([metadados PyPI](https://pypi.org/project/filelock/4.2.1/)). Uma tentativa isolada com a última3.x compatível,3.32.7, ainda reportou13 vulnerabilidades; o downgrade não foi aplicado. O [advisory do mantenedor](https://github.com/tox-dev/filelock/security/advisories/GHSA-2g95-wg33-c5x2) confirma um dos intervalos afetados4.1.0–4.2.0; não é o único advisory do relatório.

A ferramenta de auditoria sai do extra dev em Python3.10 por marcador de versão; as dependências de runtime não mudam. No CI, após concluir testes/build no interpretador original, o job grava o caminho site-packages daquela execução. Só então3.10 seleciona Python3.11 para criar um venv descartável do auditor, com pip-audit2.10.1/filelock4.2.5. As outras versões também usam auditor isolado. Audita-se tanto o venv da ferramenta quanto o diretório original de pacotes, com `--path`. Não se audita um conjunto re-resolvido em Python3.11 fingindo que era3.10.

O job falha se o diretório-alvo não existir ou se purelib/platlib divergirem sem suporte explícito. Não há ignore-vuln, exclusão silenciosa de pacote vulnerável, remoção da auditoria3.10 ou mudança de requires-python. O pacote local editable continua sujeito à limitação já existente de não estar disponível no PyPI; o scan das dependências instaladas permanece.

Reproduzir em host3.10 requer primeiro instalar/testar/buildar o CLI sem o extra de auditoria; depois apontar um auditor3.11+ isolado ao site-packages real. Registrar versões e resultado de ambos os scans. O resultado remoto da matriz é necessário para concluir a compatibilidade; testes locais3.12 não substituem essa evidência.
