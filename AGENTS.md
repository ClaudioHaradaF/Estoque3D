# Agente Autônomo de Skills

Este agente gerencia automaticamente uma biblioteca de 1.273 skills especializadas para o desenvolvimento do projeto Estoque3D.

## Comportamento Autônomo

O agente opera nos seguintes modos:

### 1. Detecção Automática de Necessidade
Quando o usuário faz uma solicitação que corresponde a uma skill conhecida, o agente:
- Identifica a skill relevante pelo nome, descrição ou categoria
- Carrega automaticamente as diretrizes da skill do diretório `C:\Users\User\Documents\skills\`
- Aplica os padrões e regras da skill na execução da tarefa

### 2. Gatilhos por Palavra-Chave
O agente monitora a conversa em busca de gatilhos que indicam necessidade de uma skill específica:

| Gatilho na conversa | Skill carregada |
|---|---|
| "segurança", "auditoria", "vulnerabilidade", "hardening" | `007` (security audit) |
| "teste", "testar", "cobertura", "pytest", "unit test" | `testing-python` |
| "docker", "container", "dockerfile", "compose" | `docker-patterns` |
| "arquitetura", "arch", "design", "estrutura" | `architecture` |
| "revisão", "code review", "qualidade" | `code-review` |
| "deploy", "produção", "release", "CI/CD" | `deploy-patterns` |
| "performance", "otimização", "lag", "lento" | `performance-tuning` |
| "banco", "sql", "query", "modelo", "schema" | `database-design` |
| "git", "commit", "branch", "merge", "PR" | `git-workflow` |
| "api", "endpoint", "rota", "rest", "graphql" | `api-design` |

### 3. Uso Explícito
O usuário pode ativar qualquer skill manualmente:
- `"Ative a skill [nome]"` — carrega a skill específica
- `"Preciso de [categoria]"` — carrega skills da categoria
- `"Use a skill de [descrição]"` — busca por descrição no índice

## Mecanismo de Carregamento

Quando ativada, a skill é carregada através do seguinte processo:
1. Consulta `skills_index.json` para localizar o path da skill
2. Lê o arquivo `.md` no path correspondente
3. Incorpora as diretrizes como contexto de trabalho
4. Executa a tarefa solicitada seguindo os padrões da skill

## Gestão de Contexto

Para tarefas complexas com múltiplas skills:
- Skills são ativadas uma por vez
- Quando o histórico fica longo, o agente faz um checkpoint (resumo do progresso)
- O checkpoint é salvo em `.opencode/plans/checkpoint.md`
- Após o checkpoint, o contexto é limpo e retomado do resumo

## Skills Pré-Carregadas

As seguintes skills são carregadas automaticamente no início por serem sempre relevantes:
- `python-flask` (se disponível) — padrões Flask
- `error-handling-patterns` — tratamento de erros
- `logging-best-practices` — logging estruturado
