# Base compartilhada

## Modelos abstratos

`base.models.BaseModel` fornece `created_at` e `updated_at` para entidades persistidas. `base.models.TenantAwareModel` herda essa base e adiciona a FK obrigatória `workspace`.

Modelos concretos que pertencem a um workspace devem herdar `TenantAwareModel`. O modelo `Workspace` é a exceção: ele é a raiz do tenant e herda apenas `BaseModel`.

## Querysets e manager

`TenantQuerySet.for_tenant(workspace)` é a API explícita para limitar leituras ao workspace informado. `TenantManager` é o manager usado por `TenantAwareModel` e expõe o mesmo método.

```python
records = Task.objects.for_tenant(request.tenant)
```

O manager não aplica um tenant global implicitamente. Services, selectors e views devem informar o workspace de forma explícita para que consultas sem contexto não exponham dados.

## ContextVar

`base.managers.current_tenant` contém o workspace resolvido durante a request. O middleware define o valor e sempre restaura o token no bloco `finally`. Código fora de uma request não deve depender desse contexto; tasks Celery devem receber `workspace_id` explicitamente.

## Mixins

Use `TenantQuerysetMixin` antes de `ListView`, `DetailView` ou outra CBV que disponibilize `get_queryset()`:

```python
class TaskListView(TenantQuerysetMixin, ListView):
    model = Task
```

O mixin retorna `queryset.none()` quando não existe tenant ativo. `RoleRequiredMixin` exige usuário autenticado, membership ativa e, quando configurado, um papel permitido:

```python
class WorkspaceSettingsView(RoleRequiredMixin, TemplateView):
    allowed_roles = ('owner',)
```

`PerPageMixin` aceita somente os valores `10`, `20`, `50`, `100` e `200` em `?per_page=`. Parâmetros adicionais que precisam sobreviver à paginação devem ser declarados em `per_page_query_params`.

## Banco

`python manage.py wait_for_db` tenta abrir uma conexão com o banco padrão por até 60 segundos. Use `--timeout` e `--interval` para ajustar o comportamento de entrypoints.
