# Autenticação

## Usuário

`accounts.User` deriva de `AbstractUser`, remove `username` e usa e-mail normalizado como `USERNAME_FIELD`. O `UserManager` normaliza o endereço completo com `strip().casefold()`, cria senhas com o hasher do Django e mantém os flags de staff/superusuário protegidos.

O backend nativo `django.contrib.auth.backends.ModelBackend` continua suficiente porque o manager implementa `get_by_natural_key()` para o campo `email`.

## Cadastro

`accounts.services.create_account()` é atômico e cria:

1. usuário;
2. workspace pessoal;
3. membership com papel `owner`;
4. `UserSettings` com os defaults do produto.

A view autentica o usuário somente depois que a transação termina com sucesso. O slug do workspace recebe um sufixo curto aleatório para manter unicidade sem expor o e-mail.

## Rotas

- `/conta/login/`: login por e-mail e senha;
- `/conta/cadastro/`: cadastro;
- `/conta/logout/`: logout exclusivamente via POST;
- `/conta/senha/redefinir/`: recuperação de senha nativa do Django;
- `/conta/configuracoes/`: configurações de perfil, aparência, foco, localização e segurança;
- `/conta/configuracoes/email/`: troca de e-mail com confirmação da senha atual;
- `/conta/configuracoes/senha/`: troca de senha com preservação da sessão;
- `/conta/`: landing autenticada temporária até a implementação do dashboard.

As mensagens usam o framework nativo de messages e os formulários possuem CSRF, labels associados, erros visíveis e foco por teclado.

## Preferências

`accounts.UserSettings` pertence diretamente ao usuário, não ao workspace. O cadastro cria o registro dentro da mesma transação do usuário e do workspace. Bases existentes recebem um registro durante a migration `accounts.0002_usersettings`; a tela também possui fallback para usuários criados por integrações antigas.

O tema persistido pode ser `system`, `light` ou `dark`. O template base aplica a preferência no elemento `<html>` antes dos estilos e acompanha mudanças do tema do sistema. O timezone salvo é ativado somente durante a request e sempre é limpo ao final do ciclo.

## E-mail

O desenvolvimento usa o `console.EmailBackend` já configurado. A recuperação usa as views nativas do Django, com versões texto e HTML do e-mail. Produção deve fornecer SMTP pelas variáveis documentadas no `PRD.md`.

## Migrations

A migration `accounts.0001_initial` deve existir antes de `admin.0001` e `tenants.0001` em uma base nova. A `db.sqlite3` criada antes da Sprint 4 registra `admin.0001` antes da dependência do usuário customizado; ela não deve ser reutilizada como baseline de produção.

## Execução local

O `.env` usado pelo `runserver` fora do Docker aponta para `sqlite:///db_local.sqlite3`. O hostname `db` só é resolvido dentro da rede do Docker Compose; no Compose, mantenha a URL PostgreSQL do `.env.example`.
