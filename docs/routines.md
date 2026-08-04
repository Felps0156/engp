# Rotina semanal

## Modelo

`WeeklyRoutineItem` representa o modelo recorrente. Os dias são armazenados em
uma lista JSON canônica com inteiros de `0` (segunda-feira) a `6` (domingo).

`RoutineOccurrence` materializa uma data do modelo e copia título, horário,
categoria, cor, estimativa e prioridade. A constraint única em
`(routine_item, occurrence_date)` torna a geração idempotente. Alterar um item
não reescreve ocorrências já materializadas.

Itens pausados não geram novas ocorrências. A exclusão de um item com qualquer
ocorrência é protegida pelo relacionamento `PROTECT`; nesses casos, pause o
item para preservar o histórico.

## Interface

- `GET /rotina/` exibe segunda-feira a domingo.
- `GET /rotina/novo/` cria um item recorrente.
- A edição mantém os snapshots já gerados.
- Pausar, reativar e excluir são ações `POST` protegidas por CSRF.
- A página é tenant-aware e mostra os itens do workspace ativo.

## Geração

O command pode gerar uma data ou um intervalo:

```bash
python manage.py generate_routine_occurrences
python manage.py generate_routine_occurrences --start 2026-08-03 --end 2026-08-09
python manage.py generate_routine_occurrences --workspace-id 1
```

O command não depende de contexto de request. Ele considera apenas itens
ativos, workspaces ativos, o intervalo de validade e os dias selecionados.
