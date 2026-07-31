# Multi-tenancy por workspace

## Modelo

O ENGP usa banco e schema compartilhados. `Workspace` é o tenant raiz e `WorkspaceMembership` liga um usuário a um workspace com papel `owner` ou `member`.

Uma membership possui unicidade por `(workspace, user)`, papel validado por constraint e índices para consultas por workspace, usuário e status ativo.

`WorkspaceMembership.user` usa `settings.AUTH_USER_MODEL` desde já. A Sprint 4 ainda precisa criar o `accounts.User` customizado e definir `AUTH_USER_MODEL` antes de estabelecer uma migration baseline para produção; o banco SQLite local desta fundação é descartável.

## Resolução durante a request

`tenants.middleware.TenantMiddleware` deve ficar depois de `AuthenticationMiddleware`. Para usuário autenticado, ele:

1. considera somente memberships ativas;
2. considera somente workspaces ativos;
3. usa `request.session['active_workspace_id']` quando o usuário possui essa membership;
4. caso contrário, escolhe a primeira membership por `workspace_id` de forma determinística;
5. define `request.tenant` e `request.membership`;
6. define `current_tenant` somente durante a request e limpa o contexto no `finally`.

Usuários anônimos ou sem membership ativa recebem `request.tenant = None`. O middleware não concede acesso por ID enviado pelo cliente: qualquer workspace selecionado é validado pela membership do usuário.

## Defesa em profundidade

- Toda entidade sensível deve carregar FK `workspace`.
- Consultas devem usar `for_tenant()` ou `TenantQuerysetMixin`.
- Services devem receber `workspace` explicitamente.
- Forms e validações devem confirmar que objetos relacionados pertencem ao mesmo workspace.
- Tasks assíncronas devem receber `workspace_id` e `user_id`; nunca devem depender de `current_tenant`.
- Downloads futuros devem validar usuário, workspace e permissão antes de entregar arquivos.
- Admin não-superusuário pode apenas visualizar os workspaces em que possui membership ativa.

IDs previsíveis nunca substituem a verificação de ownership. A existência de uma FK ou de um filtro no middleware isoladamente não é suficiente.
