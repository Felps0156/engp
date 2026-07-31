# Categorias

`categories.Category` é uma entidade `TenantAwareModel`: cada registro pertence a um `Workspace` e nenhuma rota recebe o workspace pelo formulário. O tenant ativo vem do middleware e é aplicado ao queryset das telas de listagem, edição e exclusão.

## Regras

- nomes são normalizados com espaços externos removidos;
- nomes são únicos por workspace sem diferenciar maiúsculas e minúsculas;
- o slug é derivado do nome e mantido único por workspace;
- `color_token` aceita somente tokens registrados no design system;
- as categorias padrão são `Estudos`, `Trabalho`, `Pessoal` e `Saúde`;
- categorias padrão são criadas de forma idempotente no cadastro e na migration;
- a exclusão é uma operação POST com confirmação no cliente;
- excluir uma categoria não remove tarefas ou rotinas futuras que a referenciem; os relacionamentos devem usar `SET_NULL` quando forem implementados.

## Rotas

- `/categorias/`: listagem do workspace ativo;
- `/categorias/nova/`: criação;
- `/categorias/<id>/editar/`: edição com lookup tenant-aware;
- `/categorias/<id>/excluir/`: exclusão POST tenant-aware.

As rotas exigem usuário autenticado com membership ativa. O model e o formulário também validam a unicidade para evitar que IDs ou requests concorrentes atravessem o isolamento do workspace.
