# ADR 004: Plataforma em um repositório, produtos separados, harness como artefato

Status: aceita (estratégia). Nome do repositório, layout final e calendário: a confirmar (ver `docs/PLATFORM-MONOREPO-MIGRATION.md`).

## Contexto

Contrato e implementação mudam juntos, mas viviam em quatro repositórios (kit, harness, cli, engineering-team). Efeitos observados: uma mudança de contrato exige várias tarefas, branches e PRs em sequência manual; o `ai-team` opera um único repositório por `init`; houve duplicação (skills entre kit e engineering-team, vocabulário do ProductEvent no kit e no harness, handoff dividido em dois schemas); a troca de nomes legados ficou incompleta. O harness é runtime embutido nos produtos e é consumido por versão imutável; os outros três são contratos e ferramentas de desenvolvimento.

## Decisão

1. **Plataforma em um repositório, com pacotes separados**: contratos e políticas (hoje o kit), harness, cli e engineering-team. Cada pacote mantém dono, versão, testes e release próprios.
2. **Produtos em repositórios próprios** (oito hoje). Domínio, runtime e deploy permanecem independentes.
3. **Harness como artefato**: os produtos consomem releases imutáveis com checksum, nunca o código-fonte do repositório da plataforma e nunca um branch.
4. **O product-platform-cli permanece uma capacidade separada do Atlas**: a descoberta de proposta não é absorvida pelo estágio de plano do `ai-team`. Entradas diferentes (sem repositório versus checkout fixado), objetivos diferentes (explorar e contestar versus plano executável), independência entre provedores e portão humano entre proposta e implementação.

## Regras que continuam valendo, agora por pacote

- Os ADR 001 a 003 valem com "repositório" lido como "pacote" dentro da plataforma: o pacote de contratos não depende de nenhum outro pacote; harness, cli e engineering-team dependem apenas dele; produtos dependem apenas de contratos e harness (este por artefato); produto para produto continua proibido.
- O isolamento físico deixa de proteger o grafo; ele passa a ser verificado por checagem automática e `CODEOWNERS`.
- Releases por pacote com tag própria (`harness-v*`, `cli-v*`, `engineering-team-v*`, `contracts-v*`). O CI roda por caminho alterado. O gate de release do harness é mais rígido que o das ferramentas, por rodar em produção dos produtos.

## Consequências

- Positivas: uma mudança de contrato e implementação vira um PR e uma tarefa do `ai-team`; some a duplicação entre pacotes; uma só camada de provedores e de CI.
- Custos: migração com histórico, reescrita de CI e releases, atualização de referências e do pin do primeiro consumidor (`vehicle-tracking`), e disciplina para manter fronteiras sem isolamento físico.
- Riscos: acoplamento acidental entre ferramentas de desenvolvimento e o runtime dos produtos; mitigado pelas regras de release por pacote e pelo consumo por artefato.

## Quando reavaliar

Equipes ou permissões distintas por pacote, consumidores externos dos pacotes, ou ritmos de release incompatíveis dentro do repositório.
