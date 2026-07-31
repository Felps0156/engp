# PRD — ENGP — Sistema de Produtividade Pessoal

> **Versão:** 1.0  
> **Data:** 2026-07-30  
> **Status:** pronto para planejamento e desenvolvimento  
> **Nome do produto:** `ENGP`  
> **Slug Python:** `engp`  
> **Slug Docker:** `engp`  
> **Domínio local:** `engp.localhost`  
> **Domínio de produção:** `<DOMINIO_DO_SISTEMA>` (pendente de decisão operacional)  
> **Registry:** `ghcr.io/Felps0156/engp`  
> **Stack núcleo:** Python 3.13+ · Django 6.0+ · PostgreSQL 16 · Celery · RabbitMQ · Redis · Docker Swarm · Traefik · LangChain 1.0+ · LangGraph

---

## 0. Sobre este documento

Este documento é a fonte única de verdade para o desenvolvimento do sistema. Ele deve ser citado como `@PRD.md` em prompts de implementação, revisões técnicas, criação de sprints e decisões de arquitetura.

### 0.1 Convenções

- Produto, documentação funcional e interface: português brasileiro.
- Código, nomes de apps, classes, models, campos, funções e variáveis: inglês.
- Código Python com aspas simples e conformidade com PEP 8.
- Diagramas técnicos em Mermaid.
- Tarefas de sprint e critérios de aceite em checklists Markdown `- [ ]`.
- Toda alteração de escopo deve atualizar este PRD antes da implementação.
- O arquivo `requirements.txt` deve usar versões fixadas e permanecer atualizado.
- O projeto não terá suíte de testes automatizados no MVP, conforme restrição do projeto. Validações manuais, smoke checks e critérios de aceite continuam obrigatórios.
- Placeholders entre `< >` em instruções de deploy são entradas operacionais intencionais; não representam valores válidos de desenvolvimento ou produção até serem substituídos.

### 0.2 Adaptação do projeto SCSI

O repositório público `pycodebr/scsi`, branch `main`, é a referência de arquitetura e operação. Os seguintes padrões devem ser reaproveitados e adaptados:

- projeto Django organizado por apps de domínio na raiz;
- projeto principal chamado `core`;
- app compartilhada chamada `base`;
- usuário customizado autenticado por e-mail;
- model abstrata com `created_at` e `updated_at`;
- model abstrata tenant-aware;
- `TenantManager`, `TenantQuerysetMixin`, middleware de tenant e defesa em profundidade;
- um único `settings.py` carregado por `django-environ`;
- Celery com RabbitMQ como broker e Redis como result backend/cache;
- entrypoints separados para web e Celery;
- endpoint `/health/` sem acesso ao banco;
- migrations protegidas por advisory lock do PostgreSQL;
- `collectstatic --clear` somente no entrypoint web;
- Docker Compose para desenvolvimento;
- Docker Swarm e Traefik para produção;
- TLS wildcard com DNS-01 do Cloudflare;
- três redes: pública, interna isolada e egress;
- deploy por script, backups e documentação com MKDocs.

### 0.3 Decisão de normalização de escopo

O briefing original mistura um produto de produtividade pessoal com termos herdados de uma plataforma para corretoras de seguros. Para manter coerência:

- o tenant será um **Workspace**, não uma corretora;
- cada conta cria automaticamente um workspace pessoal;
- o banco continuará preparado para vários usuários por workspace;
- no MVP, não haverá tela de equipe, convites ou cobrança por workspace;
- tarefas, rotinas, sessões de foco, notas, categorias e notificações sempre pertencem a um workspace;
- dentro do workspace, os dados pessoais também terão vínculo com o usuário quando necessário.

### 0.4 Identidade e domínio

- O nome oficial do produto nesta fase é `ENGP — Sistema de Produtividade Pessoal`.
- O slug técnico único para Python, serviços Docker e imagem GHCR é `engp`.
- `engp.localhost` é o domínio canônico de desenvolvimento local e não deve ser usado em produção.
- O domínio de produção ainda não foi informado. O placeholder `<DOMINIO_DO_SISTEMA>` permanece somente nas instruções que precisam desse valor para o deploy.

---

## Índice

1. Visão geral do produto  
2. Problema e proposta de valor  
3. Objetivos e métricas  
4. Escopo do MVP  
5. Fora do escopo  
6. Público-alvo e personas  
7. Jornadas principais  
8. Regras gerais do produto  
9. Arquitetura geral  
10. Multi-tenancy  
11. Stack técnica  
12. Estrutura do projeto  
13. Apps Django  
14. Modelagem de dados  
15. Autenticação e onboarding  
16. Home  
17. Rotina semanal  
18. Planejamento de tarefas  
19. Foco/Pomodoro  
20. Bloco de notas  
21. Configurações  
22. Categorias  
23. Notificações  
24. Inteligência artificial  
25. Regras de analytics  
26. Design system e UI/UX  
27. Acessibilidade e responsividade  
28. Segurança  
29. Arquivos e mídias  
30. Tasks assíncronas  
31. E-mails  
32. Performance e cache  
33. Logs e observabilidade  
34. Documentação  
35. Variáveis de ambiente e secrets  
36. Desenvolvimento local com Docker Compose  
37. Arquitetura de produção  
38. Docker Stack  
39. Guia de deploy do zero  
40. Backup e restauração  
41. Rollback e recuperação  
42. Dados de demonstração  
43. Critérios gerais de aceite  
44. Riscos e decisões técnicas  
45. Roadmap  
46. Sprints de implementação  
47. Definition of Done  
48. Checklist de lançamento

---

## 1. Visão geral do produto

### 1.1 Descrição

`ENGP` é uma aplicação web de produtividade que ajuda o usuário a transformar compromissos, objetivos e responsabilidades em tarefas executáveis, estruturar uma rotina semanal, realizar sessões de foco e acompanhar o progresso sem excesso de configuração.

O produto deve combinar quatro ideias principais:

1. capturar tarefas rapidamente;
2. planejar o que será feito hoje e durante a semana;
3. executar com foco por meio de um cronômetro integrado;
4. revisar o progresso usando métricas simples e úteis.

### 1.2 Princípio central

O sistema não deve se transformar em um gerenciador complexo de projetos. O MVP deve ser pessoal, direto e de baixa fricção. Toda funcionalidade deve responder a pelo menos uma destas perguntas:

- O que preciso fazer?
- O que faço agora?
- Qual rotina está prevista para hoje?
- Quanto consegui concluir e focar?

---

## 2. Problema e proposta de valor

### 2.1 Problema

Usuários costumam distribuir sua rotina entre notas, calendário, listas soltas e cronômetros separados. Isso causa:

- tarefas esquecidas ou não planejadas;
- excesso de decisões antes de começar;
- dificuldade de transformar rotina em ações diárias;
- pouca relação entre planejamento e execução;
- métricas fragmentadas;
- interfaces com informações repetidas e distrações.

### 2.2 Proposta de valor

O produto entrega um fluxo único:

```text
Capturar → Planejar → Executar com foco → Concluir → Revisar progresso
```

O diferencial do MVP é a integração entre tarefas, rotina semanal e sessões de foco, com uma Home de desktop inteira dentro do viewport e sem gráficos redundantes.

---

## 3. Objetivos e métricas

### 3.1 Objetivos de produto

- Permitir que um novo usuário crie a primeira tarefa em menos de dois minutos.
- Exibir com clareza as prioridades do dia.
- Reduzir a fricção para iniciar uma sessão de foco.
- Transformar a rotina semanal em ocorrências diárias rastreáveis.
- Consolidar tarefas concluídas e minutos de foco em um único gráfico semanal.
- Manter a interface simples, previsível e consistente.

### 3.2 Indicadores do produto

- `activation_rate`: percentual de usuários que concluem onboarding e criam a primeira tarefa.
- `daily_planned_tasks`: tarefas planejadas para o dia.
- `daily_completed_tasks`: tarefas concluídas no dia.
- `focus_minutes`: minutos efetivamente focados.
- `focus_completion_rate`: sessões finalizadas / sessões iniciadas.
- `routine_completion_rate`: ocorrências concluídas / ocorrências previstas.
- `weekly_active_days`: dias com ao menos uma conclusão ou sessão finalizada.

### 3.3 Metas iniciais de referência

As metas abaixo são hipóteses e devem ser revistas após uso real:

- onboarding concluído por pelo menos 70% dos novos cadastros;
- primeira tarefa criada por pelo menos 80% dos usuários que concluem onboarding;
- início de foco em até dois cliques a partir da Home;
- carregamento da Home em até dois segundos no cenário de referência;
- nenhuma exposição de dados entre workspaces.

---

## 4. Escopo do MVP

### 4.1 Funcionalidades incluídas

- cadastro, login, logout e recuperação de senha por e-mail;
- onboarding inicial pulável;
- workspace pessoal criado automaticamente;
- Home de tela única em desktop;
- tarefas com quatro visualizações baseadas em filtros;
- categorias;
- rotina semanal e ocorrências diárias;
- Pomodoro integrado a tarefas e ocorrências de rotina;
- estatísticas de foco;
- bloco de notas com editor simples;
- busca nas notas e fixação no topo;
- configurações de conta, aparência, foco e localização;
- notificações internas;
- envio de e-mails pelo Django;
- infraestrutura assíncrona com Celery, RabbitMQ e Redis;
- documentação com MKDocs;
- Docker Compose local;
- deploy em Docker Swarm com Traefik e Cloudflare;
- seed de dados de demonstração.

### 4.2 Funcionalidade de IA controlada por feature flag

O MVP técnico poderá incluir um assistente opcional para decompor uma descrição livre em sugestão de tarefa. Essa função deverá ficar desligada por padrão até validação do identificador do modelo e dos custos.

A IA nunca deve criar ou alterar dados sem revisão do usuário.

---

## 5. Fora do escopo

- colaboração em tempo real;
- convites e gestão de equipes;
- planos pagos e cobrança;
- calendário mensal completo;
- sincronização com Google Calendar, Outlook ou Apple Calendar;
- anexos em tarefas ou notas no MVP;
- subtarefas;
- dependências entre tarefas;
- projetos complexos;
- tags simultâneas a categorias;
- prioridade urgente;
- gamificação, pontos, ranking ou comparação entre usuários;
- paletas personalizadas;
- fontes customizáveis;
- widgets reposicionáveis;
- aplicativos móveis nativos;
- notificações push de navegador;
- testes automatizados;
- Kubernetes.

---

## 6. Público-alvo e personas

### 6.1 Público-alvo

Estudantes, profissionais e usuários que desejam organizar vida pessoal, estudos, trabalho e saúde sem usar um sistema complexo de gestão de projetos.

### 6.2 Persona principal — estudante organizado

- precisa conciliar aulas, provas, trabalhos e estudos;
- possui pouco tempo diário;
- quer saber rapidamente o que fazer hoje;
- se distrai com facilidade;
- prefere uma rotina visual e sessões de foco.

### 6.3 Persona secundária — profissional individual

- organiza tarefas de trabalho e pessoais no mesmo sistema;
- precisa capturar demandas rapidamente;
- valoriza uma visão semanal simples;
- quer revisar produtividade sem relatórios excessivos.

---

## 7. Jornadas principais

### 7.1 Novo usuário

```mermaid
flowchart TD
    A[Landing ou login] --> B[Criar conta]
    B --> C[Workspace pessoal criado]
    C --> D[Onboarding]
    D --> E[Selecionar áreas]
    E --> F[Definir foco padrão]
    F --> G[Criar primeira tarefa]
    G --> H[Home]
```

### 7.2 Captura e planejamento

```mermaid
flowchart LR
    A[Capturar tarefa] --> B[Caixa de entrada]
    B --> C[Definir data]
    C --> D[Hoje ou esta semana]
    D --> E[Executar]
    E --> F[Concluir]
```

### 7.3 Rotina semanal

```mermaid
flowchart LR
    A[Criar item de rotina] --> B[Selecionar dias]
    B --> C[Gerar ocorrência diária]
    C --> D[Exibir na Home]
    D --> E{Ação}
    E -->|Concluir| F[Registrar conclusão]
    E -->|Pular| G[Registrar como pulada]
    E -->|Foco| H[Iniciar sessão]
```

### 7.4 Sessão de foco

```mermaid
flowchart LR
    A[Escolher tarefa ou rotina] --> B[Escolher duração]
    B --> C[Iniciar]
    C --> D[Pausar ou continuar]
    D --> E[Finalizar]
    E --> F[Registrar duração efetiva]
    F --> G[Atualizar estatísticas]
```

---

## 8. Regras gerais do produto

- Todas as datas devem respeitar o fuso horário configurado pelo usuário.
- O fuso padrão é `America/Sao_Paulo`.
- A interface deve usar português brasileiro.
- O código deve usar inglês.
- Toda entidade persistida deve ter `created_at` e `updated_at`.
- Exclusões destrutivas devem pedir confirmação.
- Operações idempotentes não podem duplicar ocorrências, notificações ou sessões.
- O sistema deve usar mensagens claras de sucesso, erro e validação.
- A Home não deve repetir a mesma métrica em vários gráficos.
- Rotina não é um segundo sistema de tarefas.
- Visualizações de tarefas são filtros da mesma tabela.
- Sessão de foco cancelada não soma minutos focados.
- Sessão pausada não acumula tempo durante a pausa.
- Alterar uma rotina só afeta ocorrências futuras.
- Dados históricos não devem ser reescritos por alterações posteriores.

---

## 9. Arquitetura geral

### 9.1 Estilo arquitetural

Monólito modular Django, organizado por domínio, com processamento assíncrono externo ao processo web.

```mermaid
flowchart TB
    U[Usuário] --> CF[Cloudflare DNS/Proxy]
    CF --> T[Traefik]
    T --> A1[Django App Replica 1]
    T --> A2[Django App Replica 2]
    A1 --> DB[(PostgreSQL)]
    A2 --> DB
    A1 --> R[(Redis)]
    A2 --> R
    A1 --> MQ[(RabbitMQ)]
    A2 --> MQ
    MQ --> CW[Celery Workers]
    CW --> DB
    CW --> R
    CB[Celery Beat] --> MQ
    CW --> API[APIs externas]
```

### 9.2 Camadas

- **Templates/UI:** Django Templates, HTML, CSS e JavaScript progressivo.
- **Views:** preferencialmente Class Based Views.
- **Forms:** validação de entrada e mensagens em pt-BR.
- **Services:** regras de negócio com mais de uma operação ou transação.
- **Models:** invariantes simples, relacionamentos e constraints.
- **Selectors:** consultas de leitura complexas e analytics.
- **Tasks:** operações assíncronas idempotentes.
- **Agents:** grafos LangGraph e ferramentas explicitamente tenant-aware.

### 9.3 Regras contra overengineering

- Não criar API REST no MVP sem necessidade real.
- Não criar repositórios genéricos sobre o ORM.
- Não criar event bus interno.
- Não usar microserviços.
- Não usar signals para regras centrais de negócio.
- Usar signals somente para efeitos simples e documentados.
- Preferir transações explícitas nos services.

---

## 10. Multi-tenancy

### 10.1 Modelo

Shared database e shared schema, com isolamento por chave estrangeira `workspace`.

### 10.2 Entidades-base

```python
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantAwareModel(BaseModel):
    workspace = models.ForeignKey(
        'tenants.Workspace',
        on_delete=models.CASCADE,
        db_index=True,
    )

    class Meta:
        abstract = True
```

### 10.3 Resolução do tenant

- usuário autenticado deve possuir uma membership ativa;
- o middleware define `request.tenant`;
- o tenant ativo também pode ser armazenado em `ContextVar` durante a request;
- views sensíveis devem herdar de `TenantQuerysetMixin`;
- services devem receber `workspace` explicitamente;
- tasks Celery devem receber `workspace_id` e `user_id` explicitamente;
- nenhuma task deve depender de contexto de request.

### 10.4 Defesa em profundidade

O isolamento não pode depender de uma única camada:

1. FK `workspace` em toda model sensível;
2. índices compostos iniciando por `workspace` nas consultas frequentes;
3. middleware validando membership;
4. mixin de queryset;
5. services com workspace explícito;
6. validação de objetos relacionados no `clean()` ou form;
7. checagem de tenant em downloads;
8. admin restrito ou filtrado.

### 10.5 Membership

No MVP:

- todo cadastro cria um workspace pessoal;
- o usuário recebe papel `owner`;
- o sistema suporta mais de um membro tecnicamente;
- não existe UI de convite ou equipe.

---

## 11. Stack técnica

### 11.1 Backend

- Python 3.13+;
- Django 6.0+;
- PostgreSQL 16;
- psycopg 3;
- django-environ;
- Gunicorn;
- WhiteNoise;
- Pillow somente se uma funcionalidade de imagem exigir.

### 11.2 Processamento assíncrono

- Celery;
- RabbitMQ como broker;
- Redis como result backend e cache;
- django-celery-beat;
- django-celery-results;
- dj-celery-panel.

### 11.3 IA

- LangChain 1.0+;
- LangGraph;
- pacote oficial da OpenAI;
- modelo configurável por `OPENAI_MODEL`;
- identificador solicitado: `gpt-5.5-mini`, sujeito a validação de disponibilidade antes da ativação.

### 11.4 Relatórios e documentação

- ReportLab;
- PyPDF;
- MKDocs;
- Material for MkDocs;
- suporte Mermaid.

### 11.5 Infraestrutura

- Docker;
- Docker Compose;
- Docker Swarm;
- Traefik 3;
- GHCR;
- Cloudflare DNS;
- Let's Encrypt DNS-01.

---

## 12. Estrutura do projeto

```text
engp/
├── .env.example
├── .gitignore
├── .dockerignore
├── Dockerfile
├── docker-compose.yml
├── docker-stack.yml
├── entrypoint.sh
├── worker-entrypoint.sh
├── manage.py
├── requirements.txt
├── mkdocs.yml
├── PRD.md
├── core/
│   ├── __init__.py
│   ├── asgi.py
│   ├── celery.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── base/
│   ├── management/commands/
│   ├── managers.py
│   ├── mixins.py
│   ├── models.py
│   ├── services.py
│   ├── selectors.py
│   └── tasks.py
├── tenants/
├── accounts/
├── onboarding/
├── dashboard/
├── categories/
├── tasks/
├── routines/
├── focus/
├── notes/
├── notifications/
├── ai_agents/
├── reports/
├── templates/
├── static/
├── staticfiles/
├── media/
├── design_system/
│   ├── design-system.html
│   ├── tokens.css
│   ├── breakpoints.md
│   ├── THIRD_PARTY_NOTICES.md
│   └── README.md
├── docs/
└── scripts/
    ├── deploy.sh
    ├── backup.sh
    ├── restore.sh
    └── smoke_check.sh
```

---

## 13. Apps Django

| App | Responsabilidade |
|---|---|
| `core` | settings, URLs globais, WSGI/ASGI, Celery e healthcheck |
| `base` | bases abstratas, managers, mixins, utilitários e comandos compartilhados |
| `tenants` | workspaces, memberships e middleware de tenant |
| `accounts` | usuário customizado, autenticação, perfil e preferências básicas |
| `onboarding` | fluxo inicial e progresso |
| `dashboard` | composição da Home e selectors de resumo |
| `categories` | categorias do usuário/workspace |
| `tasks` | captura, planejamento, conclusão e filtros |
| `routines` | modelos semanais e ocorrências diárias |
| `focus` | cronômetro, sessões e estatísticas |
| `notes` | editor, pesquisa e pins |
| `notifications` | notificações internas e marcação de leitura |
| `ai_agents` | grafos, schemas, tools e tasks de IA opcionais |
| `reports` | relatórios PDF futuros e exportações aprovadas |

---

## 14. Modelagem de dados

### 14.1 Diagrama de entidades

```mermaid
erDiagram
    USER ||--o{ WORKSPACE_MEMBERSHIP : belongs
    WORKSPACE ||--o{ WORKSPACE_MEMBERSHIP : has
    WORKSPACE ||--o{ CATEGORY : owns
    WORKSPACE ||--o{ TASK : owns
    WORKSPACE ||--o{ WEEKLY_ROUTINE_ITEM : owns
    WORKSPACE ||--o{ ROUTINE_OCCURRENCE : owns
    WORKSPACE ||--o{ FOCUS_SESSION : owns
    WORKSPACE ||--o{ NOTE : owns
    WORKSPACE ||--o{ NOTIFICATION : owns
    USER ||--|| USER_SETTINGS : configures
    USER ||--o{ TASK : creates
    USER ||--o{ FOCUS_SESSION : performs
    USER ||--o{ NOTE : writes
    CATEGORY ||--o{ TASK : categorizes
    CATEGORY ||--o{ WEEKLY_ROUTINE_ITEM : categorizes
    TASK ||--o{ FOCUS_SESSION : receives
    WEEKLY_ROUTINE_ITEM ||--o{ ROUTINE_OCCURRENCE : generates
    ROUTINE_OCCURRENCE ||--o{ FOCUS_SESSION : receives
```

### 14.2 `Workspace`

- `id`: BigAutoField;
- `name`: CharField(120);
- `slug`: SlugField unique;
- `is_active`: BooleanField;
- `created_at`;
- `updated_at`.

### 14.3 `WorkspaceMembership`

- `workspace`;
- `user`;
- `role`: owner/member;
- `is_active`;
- unique constraint (`workspace`, `user`).

### 14.4 `User`

Customizado a partir de `AbstractUser`:

- remover `username`;
- `email` único e obrigatório;
- `first_name`;
- `last_name`;
- `is_active`;
- `is_staff`;
- `date_joined`;
- `created_at`;
- `updated_at`;
- `USERNAME_FIELD = 'email'`;
- manager customizado.

### 14.5 `UserSettings`

- `user`: OneToOne;
- `theme`: system/light/dark;
- `timezone`: default `America/Sao_Paulo`;
- `language`: default `pt-br`;
- `date_format`;
- `time_format`;
- `default_focus_minutes`: default 25;
- `default_break_minutes`: default 5;
- `focus_end_sound_enabled`: boolean;
- `onboarding_completed`: boolean;
- timestamps.

### 14.6 `Category`

- `workspace`;
- `name`;
- `slug`;
- `color_token`: referência permitida pelo design system;
- `icon_key`: opcional;
- `is_system`: identifica categorias iniciais;
- `is_active`;
- unique constraint (`workspace`, `slug`).

Categorias iniciais:

- estudos;
- trabalho;
- pessoal;
- saúde.

### 14.7 `Task`

- `workspace`;
- `created_by`;
- `title`: obrigatório, máximo 180;
- `description`: opcional;
- `category`: nullable com `SET_NULL`;
- `priority`: low/medium/high;
- `due_date`: nullable;
- `completed_at`: nullable;
- `status`: pending/completed;
- `estimated_minutes`: opcional;
- `source`: manual/onboarding/ai;
- timestamps.

Regras:

- caixa de entrada: `due_date IS NULL` e pendente;
- hoje: `due_date <= hoje` e pendente;
- esta semana: entre hoje e hoje + 6 dias e pendente;
- concluídas: `status = completed`;
- concluir define `completed_at`;
- reabrir limpa `completed_at`;
- não criar campos diferentes para cada visualização.

### 14.8 `WeeklyRoutineItem`

- `workspace`;
- `created_by`;
- `title`;
- `category`;
- `weekdays`: JSON/lista validada ou bitmask documentado;
- `scheduled_time`: opcional;
- `estimated_minutes`;
- `priority`;
- `is_active`;
- `starts_on`;
- `ends_on`: opcional;
- timestamps.

### 14.9 `RoutineOccurrence`

- `workspace`;
- `routine_item`;
- `occurrence_date`;
- `scheduled_time_snapshot`;
- `title_snapshot`;
- `category_snapshot` ou FK preservada;
- `estimated_minutes_snapshot`;
- `priority_snapshot`;
- `status`: pending/completed/skipped;
- `completed_at`;
- `skipped_at`;
- timestamps;
- unique constraint (`routine_item`, `occurrence_date`).

Snapshots são necessários para preservar histórico quando a rotina for editada.

### 14.10 `FocusSession`

- `workspace`;
- `user`;
- `task`: opcional;
- `routine_occurrence`: opcional;
- `started_at`;
- `ended_at`: opcional;
- `planned_minutes`;
- `focused_seconds`;
- `paused_seconds`;
- `status`: running/paused/completed/cancelled;
- `last_resumed_at`: opcional;
- timestamps.

Constraints:

- no máximo um entre `task` e `routine_occurrence` pode estar relacionado;
- uma sessão deve pertencer ao mesmo workspace do objeto relacionado;
- `focused_seconds >= 0`;
- `planned_minutes > 0`.

### 14.11 `Note`

- `workspace`;
- `author`;
- `title`: opcional;
- `content`: texto estruturado sanitizado;
- `plain_text`: versão para busca;
- `is_pinned`;
- `pinned_at`: opcional;
- timestamps.

### 14.12 `Notification`

- `workspace`;
- `user`;
- `type`;
- `title`;
- `message`;
- `url`: opcional e validado como URL interna;
- `is_read`;
- `read_at`;
- `metadata`: JSON;
- timestamps.

---

## 15. Autenticação e onboarding

### 15.1 Autenticação

O usuário pode:

- criar conta;
- entrar com e-mail e senha;
- sair;
- recuperar senha;
- editar nome e informações básicas;
- alterar e-mail com confirmação de senha;
- alterar senha;
- excluir conta com confirmação.

### 15.2 Cadastro

Ao cadastrar:

1. validar e-mail normalizado;
2. criar `User`;
3. criar `Workspace` pessoal;
4. criar membership owner;
5. criar configurações iniciais;
6. criar categorias iniciais;
7. autenticar o usuário;
8. redirecionar ao onboarding.

A operação deve ser atômica.

### 15.3 Onboarding

Etapas:

1. nome;
2. principais áreas;
3. duração padrão do foco;
4. primeira tarefa;
5. item opcional da rotina semanal.

Regras:

- pode ser pulado;
- deve salvar progresso por etapa;
- não pode criar categorias duplicadas;
- ao concluir ou pular, marcar `onboarding_completed=True`;
- usuários que já concluíram não devem ser forçados a repetir.

### 15.4 Critérios de aceite

- [ ] Cadastro usa e-mail, sem username.
- [ ] Workspace pessoal é criado na mesma transação.
- [ ] Primeiro login redireciona ao onboarding.
- [ ] Onboarding pode ser pulado.
- [ ] Recuperação de senha usa views nativas do Django.
- [ ] Usuário não acessa dados de outro workspace.

---

## 16. Home

### 16.1 Objetivo

Responder rapidamente: “O que devo fazer hoje e como está meu progresso?”

### 16.2 Conteúdo

- saudação com nome;
- data atual;
- até três tarefas de hoje;
- rotina prevista para o dia;
- botão principal “Iniciar foco”;
- tarefas concluídas hoje;
- minutos focados hoje;
- gráfico dos últimos sete dias com duas séries.

### 16.3 Regra de tela única

Em desktop, a Home deve caber no viewport sem rolagem vertical nas resoluções de referência:

- 1366 × 768;
- 1440 × 900;
- 1920 × 1080;
- zoom do navegador em 100%.

Contrato de layout:

```css
.app-shell {
    min-height: 100dvh;
}

.dashboard-main {
    height: calc(100dvh - var(--app-header-height));
    overflow: hidden;
}
```

Regras adicionais:

- usar grid responsivo com `minmax(0, 1fr)`;
- limitar tarefas a três;
- limitar ocorrências de rotina e oferecer “Ver rotina”;
- usar cards compactos;
- não usar margens verticais excessivas;
- gráfico deve redimensionar dentro do card;
- em tablet, mobile, zoom ampliado ou altura insuficiente, permitir scroll para preservar acessibilidade e conteúdo.

### 16.4 Gráfico semanal

Um único gráfico mostra, por dia:

- quantidade de tarefas concluídas;
- minutos de foco.

Pode usar dois eixos somente se o design permanecer legível. A alternativa recomendada é gráfico combinado com barras para tarefas e linha para minutos.

### 16.5 Estados

- sem tarefas: CTA para criar tarefa;
- sem rotina: CTA para configurar rotina;
- sem histórico: gráfico zerado, sem erro;
- carregamento: skeleton conforme design system;
- erro parcial: demais cards continuam disponíveis.

### 16.6 Critérios de aceite

- [ ] Desktop de referência não possui scroll vertical.
- [ ] Home mostra no máximo três tarefas.
- [ ] Há apenas um gráfico semanal.
- [ ] Botão de foco está visível sem scroll.
- [ ] Mobile pode rolar normalmente.
- [ ] Nenhuma consulta da Home ignora workspace.

---

## 17. Rotina semanal

### 17.1 Conceito

Rotina semanal é um modelo recorrente que gera ocorrências diárias. Não é uma segunda tabela de tarefas.

### 17.2 Visualização

A página deve mostrar os sete dias:

- segunda;
- terça;
- quarta;
- quinta;
- sexta;
- sábado;
- domingo.

Em desktop, usar colunas ou grade. Em mobile, usar tabs, accordions ou cartões empilhados.

### 17.3 Ações

- criar item;
- editar item;
- pausar;
- reativar;
- excluir;
- concluir ocorrência;
- pular ocorrência;
- iniciar foco.

### 17.4 Geração de ocorrências

- Celery Beat executa diariamente pouco após meia-noite no timezone do sistema;
- gera ocorrências para a data atual;
- command manual permite gerar por intervalo;
- operação é idempotente;
- unique constraint impede duplicidade;
- ao acessar a Home, um fallback síncrono pode garantir as ocorrências do dia do usuário caso a task esteja atrasada;
- somente itens ativos e válidos na data geram ocorrência.

### 17.5 Edição

- mudanças afetam somente ocorrências futuras pendentes ainda não materializadas;
- ocorrências já criadas mantêm snapshots;
- exclusão deve ser protegida quando houver histórico: preferir soft disable ou `PROTECT`/confirmação adequada.

---

## 18. Planejamento de tarefas

### 18.1 Visualizações

As quatro visualizações são filtros da mesma model:

1. Caixa de entrada;
2. Hoje;
3. Esta semana;
4. Concluídas.

### 18.2 Caixa de entrada

- tarefas pendentes sem `due_date`;
- ação rápida “Planejar para hoje”;
- ação de selecionar outra data.

### 18.3 Hoje

- tarefas do dia;
- tarefas atrasadas;
- atrasadas devem ser diferenciadas visualmente sem criar prioridade nova.

### 18.4 Esta semana

- próximos sete dias incluindo hoje;
- agrupar por data quando útil;
- evitar calendário mensal.

### 18.5 Concluídas

- histórico ordenado por `completed_at` decrescente;
- reabrir tarefa;
- paginação.

### 18.6 Campos

- título;
- descrição opcional;
- categoria;
- prioridade baixa, média ou alta;
- data de conclusão planejada;
- estimativa opcional.

### 18.7 Ações

- criar;
- editar;
- excluir;
- concluir;
- reabrir;
- planejar para hoje;
- mover para data;
- iniciar foco;
- filtrar por categoria;
- filtrar por prioridade.

### 18.8 Validações

- título obrigatório e sem espaços apenas;
- data deve ser válida no timezone do usuário;
- categoria deve pertencer ao mesmo workspace;
- filtros devem preservar query params na paginação;
- conclusão repetida deve ser idempotente.

---

## 19. Foco/Pomodoro

### 19.1 Início

O usuário pode iniciar a partir:

- de uma tarefa;
- de uma ocorrência de rotina;
- do botão global, escolhendo um item;
- sem item relacionado, caso o produto mantenha esta opção habilitada.

### 19.2 Durações

- 25 minutos;
- 40 minutos;
- 50 minutos;
- tempo personalizado.

### 19.3 Máquina de estados

```mermaid
stateDiagram-v2
    [*] --> Running
    Running --> Paused: pausar
    Paused --> Running: continuar
    Running --> Completed: finalizar
    Paused --> Completed: finalizar
    Running --> Cancelled: cancelar
    Paused --> Cancelled: cancelar
    Completed --> [*]
    Cancelled --> [*]
```

### 19.4 Cronometragem confiável

A fonte de verdade não deve ser um contador decrementado apenas no navegador.

- persistir timestamps no backend;
- cliente calcula tempo restante usando timestamps;
- ao recarregar, reconstruir estado;
- ao pausar, acumular tempo efetivo;
- ações críticas usam endpoint POST com CSRF;
- impedir duas sessões `running/paused` simultâneas por usuário;
- considerar lock transacional ao iniciar.

### 19.5 Modo imersivo

Mostrar apenas:

- título;
- tempo restante;
- pausar/continuar;
- finalizar;
- sair/cancelar.

O restante da interface fica escurecido. Não esconder controles essenciais de acessibilidade.

### 19.6 Registro

Ao finalizar:

- objeto relacionado;
- início;
- término;
- duração planejada;
- duração efetiva;
- status.

### 19.7 Estatísticas

- tempo hoje;
- tempo na semana;
- quantidade de sessões;
- tempo por categoria;
- histórico.

Somente sessões `completed` entram nas métricas principais.

---

## 20. Bloco de notas

### 20.1 Funcionalidades

- criar nota;
- editar;
- excluir;
- texto com títulos, listas e marcadores;
- pesquisa rápida;
- fixar e desafixar;
- ordenar fixadas primeiro e depois por atualização.

### 20.2 Editor

O MVP deve usar uma solução simples e sanitizada. Não armazenar HTML arbitrário sem limpeza.

Opções aceitas:

- Markdown controlado;
- editor estruturado com JSON validado;
- HTML sanitizado por biblioteca aprovada.

### 20.3 Pesquisa

- pesquisar título e `plain_text`;
- usar `icontains` inicialmente;
- criar índice e migrar para full-text do PostgreSQL somente quando necessário;
- debounce no frontend para evitar requisições excessivas.

---

## 21. Configurações

### 21.1 Conta

- editar nome;
- editar e-mail;
- alterar senha;
- excluir conta.

### 21.2 Aparência

- claro;
- escuro;
- sistema.

Persistir no banco e aplicar antes do primeiro paint sempre que possível para evitar flash de tema.

### 21.3 Foco

- duração padrão;
- duração de pausa;
- som ao encerrar.

### 21.4 Localização

- idioma pt-BR no MVP;
- timezone;
- formato de data;
- formato de horário.

### 21.5 Exclusão de conta

- exigir senha atual;
- mostrar consequências;
- encerrar sessão após exclusão;
- definir política de retenção antes de produção;
- no MVP, exclusão pode ser imediata e cascata apenas no workspace pessoal sem outros membros.

---

## 22. Categorias

### 22.1 Padrões

- estudos;
- trabalho;
- pessoal;
- saúde.

### 22.2 Personalizadas

- usuário pode criar outras categorias;
- nomes únicos por workspace ignorando maiúsculas/minúsculas;
- excluir categoria não exclui tarefas;
- ao excluir, tarefas e rotinas ficam sem categoria ou exigem substituição.

### 22.3 Regra de simplicidade

Não implementar tags no MVP.

---

## 23. Notificações

### 23.1 Casos de uso

- task assíncrona concluída;
- task assíncrona com erro tratável;
- geração de relatório;
- processamento de IA;
- lembrete interno futuro.

### 23.2 Interface

- sino no header;
- contador de não lidas;
- lista recente;
- marcar uma como lida;
- marcar todas como lidas;
- link interno seguro.

### 23.3 Entrega

No MVP, usar polling leve a cada 30–60 segundos ou atualização ao navegar. Não exigir WebSocket.

---

## 24. Inteligência artificial

### 24.1 Escopo opcional

Feature: “Organizar tarefa com IA”.

Entrada livre, por exemplo:

```text
preciso estudar biologia amanhã por umas duas horas para a prova
```

Saída sugerida:

- título;
- descrição;
- categoria;
- prioridade;
- data;
- estimativa.

### 24.2 Regras de segurança e produto

- nenhuma sugestão é salva automaticamente;
- usuário revisa e confirma;
- não enviar dados de outro workspace;
- limitar tamanho da entrada;
- não incluir segredos nos prompts;
- registrar metadados de execução, não conteúdo sensível desnecessário;
- feature flag global;
- rate limit por usuário;
- timeout e tratamento de falha;
- fallback para criação manual.

### 24.3 Grafo LangGraph

```mermaid
flowchart LR
    A[validate_input] --> B[extract_task_fields]
    B --> C[validate_schema]
    C -->|válido| D[return_draft]
    C -->|inválido| E[repair_once]
    E --> C
```

### 24.4 Estado sugerido

- `workspace_id`;
- `user_id`;
- `input_text`;
- `locale`;
- `timezone`;
- `suggestion`;
- `validation_errors`;
- `attempt_count`.

### 24.5 Modelo

- nunca hardcode em vários arquivos;
- ler `OPENAI_MODEL` do ambiente;
- usar o identificador solicitado somente após confirmação de disponibilidade;
- permitir troca sem alteração de código.

---

## 25. Regras de analytics

### 25.1 Tarefas concluídas por dia

Contar tarefas cujo `completed_at`, convertido para timezone do usuário, cai no dia.

### 25.2 Minutos de foco por dia

Somar `focused_seconds` de sessões concluídas e dividir por 60. Definir arredondamento consistente.

### 25.3 Semana

- últimos sete dias, incluindo hoje;
- não confundir com semana de calendário;
- labels curtas em pt-BR.

### 25.4 Tempo por categoria

A categoria deve ser derivada da tarefa ou rotina relacionada. Sessões sem item ficam em “Sem categoria”.

### 25.5 Cache

- cachear resumo da Home por usuário por até 60 segundos;
- invalidar ou versionar ao concluir tarefa/sessão;
- nunca compartilhar chave sem `workspace_id` e `user_id`.

---

## 26. Design system e UI/UX

### 26.1 Fonte de verdade

`@design_system/design-system.html` define:

- cores;
- tipografia;
- espaçamentos;
- bordas;
- sombras;
- ícones;
- estados;
- componentes;
- padrões de gráfico.

Os artefatos complementares são `@design_system/tokens.css`, `@design_system/breakpoints.md`, `@design_system/THIRD_PARTY_NOTICES.md` e `@design_system/README.md`. O HTML é o inventário visual; os tokens e as regras documentadas são a base para as implementações do app.

### 26.2 Regras

- não copiar visual completo de várias referências sem normalização;
- referências externas servem como matéria-prima, não como bibliotecas paralelas;
- cada elemento deve ser convertido em tokens e componentes do sistema;
- componentes equivalentes devem ter uma única implementação;
- ícones devem vir de uma única biblioteca principal;
- gráficos devem usar tokens próprios;
- estados hover/focus/disabled/error devem estar documentados.

### 26.3 Componentes mínimos

- app shell;
- header;
- sidebar ou navegação compacta;
- botão primário/secundário/ghost/danger;
- input, select, textarea, checkbox;
- modal/drawer;
- card;
- badge de prioridade;
- task row/card;
- routine item;
- timer;
- tabs/filtros;
- empty state;
- toast;
- notification item;
- chart container;
- skeleton.

---

## 27. Acessibilidade e responsividade

- navegação por teclado;
- foco visível;
- labels e mensagens de erro associadas;
- contraste adequado;
- `aria-live` para atualizações do cronômetro sem anunciar a cada segundo;
- não depender somente de cor;
- alvos de toque adequados;
- suporte a redução de movimento;
- datas e horários legíveis;
- modais com focus trap;
- Home sem scroll somente quando não comprometer zoom e acessibilidade;
- mobile-first para formulários.

---

## 28. Segurança

### 28.1 Aplicação

- CSRF ativo;
- proteção XSS;
- validação de redirect interno;
- cookies seguros em produção;
- `X_FRAME_OPTIONS = 'DENY'`;
- HSTS em produção após TLS validado;
- `SECURE_PROXY_SSL_HEADER` atrás do Traefik;
- `/health/` em `SECURE_REDIRECT_EXEMPT`;
- senha validada pelos validadores nativos;
- rate limit no Traefik e, quando necessário, na aplicação;
- páginas privadas com `LoginRequiredMixin`;
- POST para ações mutáveis;
- mensagens sem vazamento de dados.

### 28.2 Multi-tenant

- todo queryset sensível filtrado;
- IDs previsíveis não concedem acesso;
- objetos relacionados validados por workspace;
- tasks e e-mails recebem IDs e revalidam ownership;
- logs não devem registrar conteúdo de notas ou prompts completos por padrão.

### 28.3 Secrets

- `.env` sempre gitignored;
- `.env.example` sem valores reais;
- Cloudflare token em Docker Secret obrigatório;
- segredos de produção preferencialmente em Docker Secrets;
- nunca usar `source .env` em script;
- parser seguro de `KEY=VALUE`;
- rotação documentada.

---

## 29. Arquivos e mídias

O MVP não exige anexos. A infraestrutura deve seguir estes princípios caso mídia seja adicionada:

- nenhum `MEDIA_ROOT` exposto diretamente pelo Traefik;
- rota protegida valida usuário, workspace e permissão;
- nomes físicos aleatórios;
- cabeçalho `Content-Disposition` controlado;
- validar extensão, MIME e tamanho;
- não confiar no nome enviado;
- volumes persistentes no Swarm;
- backup da mídia.

---

## 30. Tasks assíncronas

### 30.1 Devem usar Celery

- geração diária de ocorrências;
- e-mails não críticos;
- IA;
- relatórios PDF;
- limpeza/rotação lógica;
- notificações derivadas;
- tarefas pesadas futuras.

### 30.2 Contrato

- idempotência;
- retries com backoff somente em erros transitórios;
- timeout;
- logs estruturados;
- `workspace_id` explícito;
- estado final registrado quando necessário;
- notificação ao usuário;
- não bloquear request.

### 30.3 UX

Ao disparar tarefa em background:

1. desabilitar botão;
2. mostrar loading curto;
3. informar que o processamento continuará;
4. devolver resposta sem esperar o processamento;
5. notificar ao concluir.

---

## 31. E-mails

- usar sistema nativo do Django;
- console backend em desenvolvimento;
- SMTP em produção;
- templates HTML e texto;
- recuperação de senha;
- mensagens transacionais futuras;
- não enviar e-mail dentro de transação antes do commit;
- usar `transaction.on_commit()` para enfileirar.

Variáveis:

- `EMAIL_BACKEND`;
- `EMAIL_HOST`;
- `EMAIL_PORT`;
- `EMAIL_HOST_USER`;
- `EMAIL_HOST_PASSWORD` ou secret;
- `EMAIL_USE_TLS`;
- `DEFAULT_FROM_EMAIL`.

---

## 32. Performance e cache

### 32.1 Banco

Índices mínimos:

- (`workspace`, `status`, `due_date`) em tarefas;
- (`workspace`, `completed_at`) em tarefas;
- (`workspace`, `occurrence_date`, `status`) em ocorrências;
- (`workspace`, `user`, `started_at`) em sessões;
- (`workspace`, `author`, `is_pinned`, `updated_at`) em notas;
- (`workspace`, `user`, `is_read`, `created_at`) em notificações.

### 32.2 Queries

- usar `select_related` para category, task e routine item;
- usar `prefetch_related` somente quando necessário;
- evitar N+1 na Home;
- limitar datasets;
- paginação nas listas históricas;
- selectors para agregações.

### 32.3 Redis

- cache da Home;
- resultados Celery;
- locks curtos quando apropriado;
- nunca usar Redis como fonte de verdade de sessões de foco.

---

## 33. Logs e observabilidade

- logs para stdout/stderr;
- formato com timestamp, nível, logger e mensagem;
- não registrar senha, token, secret ou conteúdo sensível;
- incluir `workspace_id`, `user_id`, `task_id` quando seguro;
- logs separados logicamente por Django, Celery e IA;
- access log do Traefik em JSON;
- comandos de inspeção documentados;
- healthchecks em todos os serviços.

---

## 34. Documentação

A pasta `docs/` deve conter:

- visão do produto;
- arquitetura;
- setup local;
- models;
- multi-tenancy;
- fluxo de tarefas;
- rotina;
- foco;
- Celery;
- IA;
- deploy;
- backup e restore;
- troubleshooting;
- decisões técnicas.

O `mkdocs.yml` deve usar Mermaid e navegação organizada.

---

## 35. Variáveis de ambiente e secrets

### 35.1 `.env.example`

```dotenv
# Django
DEBUG=True
SECRET_KEY=dev-only-change-me
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
LANGUAGE_CODE=pt-br
TIME_ZONE=America/Sao_Paulo
DJANGO_LOG_LEVEL=INFO

# Database
DATABASE_URL=postgres://engp:engp@db:5432/engp
POSTGRES_DB=engp
POSTGRES_USER=engp
POSTGRES_PASSWORD=engp

# Celery
CELERY_BROKER_URL=amqp://engp:engp@rabbitmq:5672//
CELERY_RESULT_BACKEND=redis://redis:6379/0
RABBITMQ_DEFAULT_USER=engp
RABBITMQ_DEFAULT_PASS=engp
REDIS_URL=redis://redis:6379/1

# E-mail
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=ENGP <no-reply@DOMINIO_DO_SISTEMA>

# OpenAI
AI_TASK_REFINEMENT_ENABLED=False
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.5-mini

# Static/media
STATIC_ROOT=/app/staticfiles
MEDIA_ROOT=/app/media

# Production
DOMAIN=<DOMINIO_DO_SISTEMA>
ACME_EMAIL=<EMAIL_DO_LETS_ENCRYPT>
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
TRAEFIK_DASHBOARD_AUTH=
GHCR_IMAGE=ghcr.io/Felps0156/engp:latest
```

### 35.2 Produção

Em produção:

```dotenv
DEBUG=False
ALLOWED_HOSTS=<DOMINIO_DO_SISTEMA>,.<DOMINIO_DO_SISTEMA>,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://<DOMINIO_DO_SISTEMA>,https://*.<DOMINIO_DO_SISTEMA>
```

Em `ALLOWED_HOSTS`, não usar esquema. Em `CSRF_TRUSTED_ORIGINS`, usar `https://`.

### 35.3 Secrets externos do Swarm

Obrigatórios:

- `CLOUDFLARE_DNS_API_TOKEN`;
- `DJANGO_SECRET_KEY`;
- `POSTGRES_PASSWORD`;
- `RABBITMQ_DEFAULT_PASS`;
- `OPENAI_API_KEY`, somente se IA ativa;
- `EMAIL_HOST_PASSWORD`, se SMTP exigir.

A aplicação deve suportar leitura por arquivo, por exemplo:

- `SECRET_KEY_FILE=/run/secrets/DJANGO_SECRET_KEY`;
- `OPENAI_API_KEY_FILE=/run/secrets/OPENAI_API_KEY`.

---

## 36. Desenvolvimento local com Docker Compose

### 36.1 Serviços

- `app`;
- `db`;
- `rabbitmq`;
- `redis`;
- `celery_worker`;
- `celery_beat`.

### 36.2 Fluxo inicial

```bash
cp .env.example .env
python -m venv .venv
```

Ativação no Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Ativação no Linux/macOS:

```bash
source .venv/bin/activate
```

Subir containers:

```bash
docker compose up --build
```

Criar superusuário:

```bash
docker compose exec app python manage.py createsuperuser
```

Carregar dados fake:

```bash
docker compose exec app python manage.py seed_demo
```

Acessos locais:

- app: `http://localhost:8000`;
- RabbitMQ: `http://localhost:15672`;
- admin: `http://localhost:8000/admin/`;
- healthcheck: `http://localhost:8000/health/`.

### 36.3 Regras do Compose

- bind mount do código somente em desenvolvimento;
- `depends_on` com healthchecks;
- PostgreSQL persistente;
- mídia persistente;
- app pode usar `runserver` localmente;
- Celery usa `worker-entrypoint.sh` e não executa migrations.

---

## 37. Arquitetura de produção

### 37.1 Serviços

- Traefik: uma réplica no manager;
- app: duas réplicas;
- PostgreSQL: uma réplica;
- RabbitMQ: uma réplica;
- Redis: uma réplica;
- Celery worker: inicialmente uma ou duas réplicas;
- Celery beat: exatamente uma réplica.

### 37.2 Redes

#### `traefik_public`

- overlay external;
- acesso externo;
- somente Traefik e app.

#### `engp_internal`

- overlay `internal: true`;
- app, db, Redis, RabbitMQ, worker e beat;
- sem saída direta à internet.

#### `engp_egress`

- overlay não interna;
- sem conexão com Traefik;
- worker e beat;
- acesso a APIs externas.

O app não precisa de egress se toda chamada externa for delegada ao Celery. Caso o app envie e-mail síncrono ou faça outra chamada externa, a decisão deve ser documentada e a rede ajustada conscientemente.

### 37.3 Volumes

- PostgreSQL;
- Redis;
- RabbitMQ;
- media;
- staticfiles;
- certificados Let's Encrypt.

---

## 38. Docker Stack

### 38.1 Traefik

- provider Swarm;
- `exposedByDefault=false`;
- portas 80 e 443;
- redirect HTTP → HTTPS;
- dashboard protegido por Basic Auth;
- Cloudflare DNS-01;
- wildcard `<DOMINIO_DO_SISTEMA>` e `*.<DOMINIO_DO_SISTEMA>`;
- token via secret e `CF_DNS_API_TOKEN_FILE`;
- confiar apenas nas faixas atuais aprovadas do Cloudflare;
- access log em JSON.

### 38.2 App

- imagem GHCR;
- Gunicorn;
- duas réplicas;
- `/health/`;
- rede pública e interna;
- `update_config.order=start-first`;
- `failure_action=rollback`;
- restart policy;
- limits e reservations;
- volumes de media e staticfiles.

Comando recomendado:

```bash
gunicorn core.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --worker-class gthread \
  --threads 2 \
  --timeout 120 \
  --max-requests 1000 \
  --max-requests-jitter 50 \
  --graceful-timeout 30 \
  --keep-alive 5 \
  --access-logfile - \
  --error-logfile -
```

Os números devem ser ajustados à RAM e CPU da VPS.

### 38.3 Healthchecks

- app: HTTP `GET /health/` sem banco;
- PostgreSQL: `pg_isready`;
- Redis: `redis-cli ping`;
- RabbitMQ: `rabbitmq-diagnostics check_port_connectivity`.

### 38.4 Entry point web

1. `wait_for_db`;
2. advisory lock PostgreSQL;
3. `migrate --noinput`;
4. liberar lock;
5. `collectstatic --noinput --clear`;
6. executar Gunicorn.

### 38.5 Entry point Celery

1. carregar secrets necessários;
2. `wait_for_db`;
3. executar worker ou beat;
4. não executar migration;
5. não executar collectstatic.

---

## 39. Guia de deploy do zero

> Substitua todos os placeholders antes de executar. Os comandos assumem Ubuntu Server recente, usuário com sudo e uma VPS limpa.

### 39.1 Preparar DNS no Cloudflare

No painel Cloudflare:

1. adicionar o domínio à conta;
2. confirmar nameservers no registrador;
3. criar registro `A` para `@` apontando ao IP público da VPS;
4. criar registro `A` ou `CNAME` para `traefik`;
5. manter proxy Cloudflare ativado somente após validar a estratégia;
6. garantir que portas 80 e 443 estejam liberadas.

### 39.2 Acessar e atualizar a VPS

```bash
ssh root@<IP_DA_VPS>
apt update
apt upgrade -y
apt install -y ca-certificates curl gnupg git ufw apache2-utils jq
```

Criar usuário de deploy:

```bash
adduser deploy
usermod -aG sudo deploy
rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy
```

Abrir firewall:

```bash
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
ufw status
```

Trocar para o usuário:

```bash
su - deploy
```

### 39.3 Instalar Docker pelo repositório oficial

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
```

```bash
. /etc/os-release
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $VERSION_CODENAME stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

```bash
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker deploy
```

Aplicar grupo sem reiniciar a VPS:

```bash
newgrp docker
```

Validar:

```bash
docker version
docker compose version
docker run --rm hello-world
```

### 39.4 Inicializar Docker Swarm

Descobrir IP da interface pública/privada usada entre nós:

```bash
hostname -I
```

Inicializar:

```bash
docker swarm init --advertise-addr <IP_DA_VPS>
```

Validar:

```bash
docker info --format '{{.Swarm.LocalNodeState}}'
docker node ls
```

### 39.5 Criar diretórios

```bash
sudo mkdir -p /opt/engp
sudo mkdir -p /backups/engp
sudo chown -R deploy:deploy /opt/engp /backups/engp
```

### 39.6 Clonar o projeto

```bash
cd /opt
git clone https://github.com/Felps0156/engp.git engp
cd /opt/engp
git checkout main
```

### 39.7 Login no GHCR

Crie um Personal Access Token com permissão adequada para packages.

```bash
export GITHUB_USER='Felps0156'
read -s GITHUB_TOKEN
echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$GITHUB_USER" --password-stdin
unset GITHUB_TOKEN
```

### 39.8 Criar redes overlay

Rede pública externa:

```bash
docker network create \
  --driver overlay \
  --attachable \
  traefik_public
```

Rede egress externa, caso o stack a declare como external:

```bash
docker network create \
  --driver overlay \
  --attachable \
  engp_egress
```

A rede interna pode ser criada pelo próprio stack. Caso seja external:

```bash
docker network create \
  --driver overlay \
  --attachable \
  --internal \
  engp_internal
```

Validar:

```bash
docker network ls
```

### 39.9 Criar token Cloudflare

No painel Cloudflare:

1. abrir perfil → API Tokens;
2. criar token customizado;
3. permissão `Zone > DNS > Edit`;
4. recurso de zona limitado a `<DOMINIO_DO_SISTEMA>`;
5. opcionalmente incluir `Zone > Zone > Read` caso a versão do provider exija descoberta;
6. copiar uma única vez;
7. não salvar no repositório.

Criar secret sem gravar no histórico:

```bash
read -s CF_TOKEN
printf '%s' "$CF_TOKEN" | docker secret create CLOUDFLARE_DNS_API_TOKEN -
unset CF_TOKEN
```

Validar:

```bash
docker secret inspect CLOUDFLARE_DNS_API_TOKEN
```

### 39.10 Criar demais secrets

Gerar Django secret:

```bash
DJANGO_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
printf '%s' "$DJANGO_KEY" | docker secret create DJANGO_SECRET_KEY -
unset DJANGO_KEY
```

PostgreSQL:

```bash
read -s POSTGRES_SECRET
printf '%s' "$POSTGRES_SECRET" | docker secret create POSTGRES_PASSWORD -
unset POSTGRES_SECRET
```

RabbitMQ:

```bash
read -s RABBITMQ_SECRET
printf '%s' "$RABBITMQ_SECRET" | docker secret create RABBITMQ_DEFAULT_PASS -
unset RABBITMQ_SECRET
```

OpenAI, somente se IA estiver ativa:

```bash
read -s OPENAI_SECRET
printf '%s' "$OPENAI_SECRET" | docker secret create OPENAI_API_KEY -
unset OPENAI_SECRET
```

SMTP, se necessário:

```bash
read -s SMTP_SECRET
printf '%s' "$SMTP_SECRET" | docker secret create EMAIL_HOST_PASSWORD -
unset SMTP_SECRET
```

Listar apenas nomes:

```bash
docker secret ls
```

### 39.11 Criar `.env` de produção

```bash
cd /opt/engp
cp .env.example .env
chmod 600 .env
nano .env
```

Conteúdo mínimo:

```dotenv
DEBUG=False
ALLOWED_HOSTS=<DOMINIO_DO_SISTEMA>,.<DOMINIO_DO_SISTEMA>,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://<DOMINIO_DO_SISTEMA>,https://*.<DOMINIO_DO_SISTEMA>
LANGUAGE_CODE=pt-br
TIME_ZONE=America/Sao_Paulo
DJANGO_LOG_LEVEL=INFO

DATABASE_URL=postgres://<DB_USER>:<DB_PASSWORD_PLACEHOLDER>@db:5432/<DB_NAME>
POSTGRES_DB=<DB_NAME>
POSTGRES_USER=<DB_USER>
POSTGRES_PASSWORD_FILE=/run/secrets/POSTGRES_PASSWORD

RABBITMQ_DEFAULT_USER=<RABBIT_USER>
RABBITMQ_DEFAULT_PASS_FILE=/run/secrets/RABBITMQ_DEFAULT_PASS
CELERY_BROKER_URL=amqp://<RABBIT_USER>:<RABBIT_PASSWORD_PLACEHOLDER>@rabbitmq:5672//
CELERY_RESULT_BACKEND=redis://redis:6379/0
REDIS_URL=redis://redis:6379/1

SECRET_KEY_FILE=/run/secrets/DJANGO_SECRET_KEY
OPENAI_API_KEY_FILE=/run/secrets/OPENAI_API_KEY
OPENAI_MODEL=gpt-5.5-mini
AI_TASK_REFINEMENT_ENABLED=False

DOMAIN=<DOMINIO_DO_SISTEMA>
ACME_EMAIL=<EMAIL_DO_LETS_ENCRYPT>
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
GHCR_IMAGE=ghcr.io/Felps0156/engp:latest
```

Observação: URLs que embutem senha exigem que a aplicação monte a URL com o secret em runtime ou use variáveis derivadas no entrypoint. Não deixar senha real no `.env` apenas para preencher `DATABASE_URL` ou `CELERY_BROKER_URL`.

### 39.12 Gerar autenticação do dashboard Traefik

```bash
read -s TRAEFIK_PASSWORD
TRAEFIK_HASH=$(htpasswd -nbB admin "$TRAEFIK_PASSWORD")
unset TRAEFIK_PASSWORD
printf '%s\n' "$TRAEFIK_HASH"
```

Copiar a saída para `TRAEFIK_DASHBOARD_AUTH` no `.env`. Preservar os caracteres `$` conforme a estratégia de interpolação documentada no stack.

### 39.13 Validar arquivos

```bash
docker compose -f docker-compose.yml config >/dev/null
```

Para stack, exportar as variáveis com parser seguro do script e validar:

```bash
./scripts/deploy.sh --check-only
```

O script deve falhar antes do deploy se:

- Swarm não estiver ativo;
- `.env` não existir;
- `DEBUG` não for `False`;
- `localhost` não estiver em `ALLOWED_HOSTS`;
- domínio estiver como placeholder;
- secrets obrigatórios não existirem;
- redes externas não existirem;
- login/push no GHCR não estiver disponível.

### 39.14 Build, push e deploy

Dar permissão:

```bash
chmod +x entrypoint.sh worker-entrypoint.sh scripts/*.sh
```

Executar:

```bash
./scripts/deploy.sh
```

O script deve:

1. carregar `.env` sem `source`;
2. validar pré-condições;
3. executar `git pull`;
4. calcular tag pelo commit SHA;
5. buildar a imagem;
6. taguear SHA e `latest`;
7. fazer push ao GHCR;
8. executar `docker stack deploy --with-registry-auth`;
9. forçar rollout de app, worker e beat;
10. imprimir status.

Redeploy sem rebuild:

```bash
./scripts/deploy.sh --skip-build
```

### 39.15 Verificar serviços

```bash
docker stack services engp
docker stack ps engp --no-trunc
```

Logs:

```bash
docker service logs -f engp_app
docker service logs -f engp_traefik
docker service logs -f engp_celery_worker
docker service logs -f engp_celery_beat
```

### 39.16 Verificar healthcheck

Internamente:

```bash
APP_CONTAINER=$(docker ps --filter name=engp_app -q | head -1)
docker exec "$APP_CONTAINER" python -c \
  "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health/').read())"
```

Externamente:

```bash
curl -I https://<DOMINIO_DO_SISTEMA>/health/
```

Resposta esperada: HTTP 200.

### 39.17 Verificar wildcard TLS DNS-01

Logs do Traefik:

```bash
docker service logs engp_traefik 2>&1 \
  | grep -Ei 'acme|certificate|cloudflare|dns'
```

Verificar certificado principal:

```bash
openssl s_client \
  -connect <DOMINIO_DO_SISTEMA>:443 \
  -servername <DOMINIO_DO_SISTEMA> \
  </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
```

Verificar subdomínio:

```bash
openssl s_client \
  -connect traefik.<DOMINIO_DO_SISTEMA>:443 \
  -servername traefik.<DOMINIO_DO_SISTEMA> \
  </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
```

O SAN deve incluir domínio raiz e wildcard.

### 39.18 Criar superusuário

```bash
APP_CONTAINER=$(docker ps --filter name=engp_app -q | head -1)
docker exec -it "$APP_CONTAINER" python manage.py createsuperuser
```

### 39.19 Smoke check

```bash
./scripts/smoke_check.sh https://<DOMINIO_DO_SISTEMA>
```

O script deve validar:

- DNS;
- HTTPS;
- `/health/`;
- página de login;
- assets estáticos;
- status das réplicas;
- conexão básica com PostgreSQL, Redis e RabbitMQ.

---

## 40. Backup e restauração

### 40.1 Backup

`scripts/backup.sh` deve:

- localizar o container/task do PostgreSQL;
- executar `pg_dump`;
- compactar;
- copiar volume de mídia;
- gerar checksum;
- registrar log;
- remover backups acima do período de retenção;
- falhar de forma clara.

Execução manual:

```bash
cd /opt/engp
BACKUP_DIR=/backups/engp ./scripts/backup.sh
```

Cron diário às 03:15:

```bash
crontab -e
```

```cron
15 3 * * * cd /opt/engp && BACKUP_DIR=/backups/engp ./scripts/backup.sh >> /var/log/engp-backup.log 2>&1
```

### 40.2 Retenção

- diários: 14 dias;
- semanais: 8 semanas;
- mensais: 6 meses, se necessário;
- cópia externa criptografada recomendada.

### 40.3 Restauração

Nunca restaurar diretamente em produção sem janela e backup atual.

Fluxo:

1. colocar aplicação em manutenção;
2. confirmar arquivo e checksum;
3. criar backup pré-restore;
4. restaurar PostgreSQL;
5. restaurar mídia;
6. executar migrations se necessário;
7. subir serviços;
8. executar smoke check;
9. remover manutenção.

Comando base:

```bash
gunzip -c /backups/engp/db_<DATA>.sql.gz \
  | docker exec -i <CONTAINER_DB> psql -U <DB_USER> -d <DB_NAME>
```

O script `restore.sh` deve exigir confirmação textual e parâmetros explícitos.

---

## 41. Rollback e recuperação

### 41.1 Rollback automático

O app deve usar:

```yaml
update_config:
  order: start-first
  failure_action: rollback
  monitor: 30s
```

### 41.2 Rollback manual de serviço

```bash
docker service rollback engp_app
```

### 41.3 Voltar para imagem anterior

```bash
docker service update \
  --image ghcr.io/Felps0156/engp:<TAG_ANTERIOR> \
  engp_app
```

Atualizar worker e beat para a mesma versão quando houver mudança de código compartilhado.

### 41.4 Migrações

- preferir migrações backward-compatible;
- separar remoção de coluna em deploy posterior;
- não depender de rollback automático de migration destrutiva;
- backup antes de mudanças de schema de alto risco.

---

## 42. Dados de demonstração

Command:

```bash
python manage.py seed_demo
```

Deve criar:

- um workspace demo;
- um usuário demo;
- quatro categorias padrão e duas personalizadas;
- tarefas sem data, de hoje, atrasadas, futuras e concluídas;
- prioridades variadas;
- rotina para todos os dias;
- ocorrências concluídas, pendentes e puladas;
- sessões de foco em sete dias diferentes;
- notas fixadas e comuns;
- notificações lidas e não lidas.

Regras:

- idempotente por identificador conhecido;
- não executar automaticamente em produção;
- suportar flag `--reset-demo` somente com confirmação.

---

## 43. Critérios gerais de aceite

### 43.1 Funcionais

- [ ] Usuário cria conta por e-mail.
- [ ] Onboarding funciona e pode ser pulado.
- [ ] Home mostra dados corretos do dia.
- [ ] Home desktop cabe no viewport de referência.
- [ ] Tarefas usam uma única model e filtros.
- [ ] Rotina gera ocorrências sem duplicar.
- [ ] Alterações de rotina preservam histórico.
- [ ] Cronômetro sobrevive a refresh.
- [ ] Pausas não contam como foco.
- [ ] Sessões canceladas não entram nas métricas.
- [ ] Notas podem ser pesquisadas e fixadas.
- [ ] Tema persiste.
- [ ] Notificações internas funcionam.

### 43.2 Segurança

- [ ] Nenhuma rota privada funciona deslogada.
- [ ] Nenhum ID de outro workspace concede acesso.
- [ ] Forms rejeitam relações de outro workspace.
- [ ] Downloads futuros são protegidos.
- [ ] `.env` não está versionado.
- [ ] secrets não aparecem em logs.
- [ ] Cloudflare token está em Docker Secret.

### 43.3 Infraestrutura

- [ ] Compose sobe localmente.
- [ ] Todos os serviços têm healthcheck aplicável.
- [ ] Swarm sobe com réplicas previstas.
- [ ] App faz rollout start-first.
- [ ] Falha de healthcheck provoca rollback.
- [ ] Celery não está na rede pública.
- [ ] Worker e beat acessam egress.
- [ ] TLS wildcard é emitido por DNS-01.
- [ ] Backup e restore foram ensaiados.

---

## 44. Riscos e decisões técnicas

| Risco | Impacto | Mitigação |
|---|---|---|
| Mistura entre rotina e tarefas | produto confuso | ocorrência separada e snapshots |
| Cronômetro depender do browser | dados incorretos | timestamps no servidor |
| Vazamento entre tenants | crítico | FK, middleware, mixins, services e validações |
| Home não caber no viewport | quebra de requisito | limites de conteúdo e layout testado |
| Celery Beat duplicar ocorrências | dados duplicados | constraint única e task idempotente |
| Modelo OpenAI indisponível | IA quebrada | env configurável, feature flag e validação |
| Secrets dentro de URLs | exposição | montar em runtime por secret files |
| Swarm ignorar `depends_on` | crash-loop | healthchecks, wait commands e restart delay |
| Migrations com duas réplicas | corrida | advisory lock |
| `collectstatic` com hashes antigos | falha de deploy | `--clear` no app |
| Banco em nó único | indisponibilidade | backup, monitoramento e plano futuro gerenciado |
| Ausência de testes automatizados | regressões | checklists manuais e smoke scripts |

### 44.1 Decisões registradas

- Monólito modular Django.
- Shared-schema multi-tenant por workspace.
- Um gráfico semanal na Home.
- Categorias sem tags.
- Rotina gera ocorrências.
- Cronômetro com fonte de verdade no backend.
- Polling em vez de WebSocket no MVP.
- Celery/RabbitMQ/Redis desde a base de infraestrutura.
- IA opcional por feature flag.
- Docker Swarm em vez de Kubernetes.

---

## 45. Roadmap

### Fase 0 — Fundação

Arquitetura, design system, ambiente, autenticação, tenant e infraestrutura local.

### Fase 1 — MVP funcional

Onboarding, categorias, tarefas, rotina, foco, Home, notas e configurações.

### Fase 2 — Operação

Notificações, Celery, documentação, seed, deploy, backup e hardening.

### Fase 3 — IA opcional

Refinamento de tarefa com LangGraph, feature flag e métricas de custo.

### Fase futura

Integrações de calendário, equipes, relatórios avançados e aplicativos móveis.

---

## 46. Sprints de implementação

### Sprint 0 — Preparação e decisões

- [x] Definir `ENGP`.
- [x] Definir slug Python e slug Docker.
- [ ] Definir domínio de produção (domínio local canônico definido como `engp.localhost`).
- [x] Criar repositório GitHub.
- [x] Copiar `PRD.md` para a raiz.
- [x] Criar `design_system/design-system.html`.
- [x] Auditar licenças de ícones, fontes e referências; referências sem licença confirmada ficam isoladas.
- [x] Registrar tokens de design.
- [x] Definir breakpoints e resoluções de Home.
- [x] Remover placeholders não usados e documentar os placeholders operacionais.

### Sprint 1 — Bootstrap Django

- [x] Criar `.venv` na raiz.
- [x] Instalar Python 3.13+.
- [x] Criar projeto Django `core`.
- [x] Manter apenas `core/settings.py`.
- [x] Criar apps na raiz.
- [x] Criar `requirements.txt` fixado.
- [x] Configurar `django-environ`.
- [x] Criar `.env.example`.
- [x] Criar `.gitignore` e `.dockerignore`.
- [x] Configurar timezone e idioma.
- [x] Configurar templates e static.
- [x] Criar `/health/` sem banco.
- [x] Configurar logging.

### Sprint 2 — Base compartilhada

- [x] Criar `BaseModel`.
- [x] Criar `TenantAwareModel`.
- [x] Criar `TenantQuerySet`.
- [x] Criar `TenantManager`.
- [x] Criar `current_tenant` com ContextVar.
- [x] Criar `TenantQuerysetMixin`.
- [x] Criar `RoleRequiredMixin` mínimo.
- [x] Criar `PerPageMixin`.
- [x] Criar command `wait_for_db`.
- [x] Documentar uso dos mixins.

### Sprint 3 — Tenants/workspaces

- [x] Criar `Workspace`.
- [x] Criar `WorkspaceMembership`.
- [x] Adicionar constraints.
- [x] Criar middleware de tenant.
- [x] Validar membership ativa.
- [x] Definir tenant em `request.tenant`.
- [x] Limpar ContextVar ao final da request.
- [x] Configurar admin seguro.
- [x] Documentar regras de tenant.

### Sprint 4 — Usuário e autenticação

- [x] Criar User antes da primeira migration definitiva.
- [x] Remover username.
- [x] Criar UserManager.
- [x] Configurar `AUTH_USER_MODEL`.
- [x] Usar o backend nativo do Django para autenticação por e-mail; backend customizado não é necessário.
- [x] Criar cadastro atômico.
- [x] Criar workspace pessoal no cadastro.
- [x] Criar membership owner.
- [x] Criar login.
- [x] Criar logout POST.
- [x] Configurar recuperação de senha.
- [x] Configurar mensagens.
- [x] Criar páginas conforme design system.

### Sprint 5 — Configurações do usuário

- [ ] Criar `UserSettings`.
- [ ] Criar criação automática explícita no cadastro.
- [ ] Implementar tema system/light/dark.
- [ ] Implementar foco padrão.
- [ ] Implementar pausa padrão.
- [ ] Implementar som.
- [ ] Implementar timezone.
- [ ] Implementar formatos de data/hora.
- [ ] Criar tela de configurações.
- [ ] Criar alteração de senha.
- [ ] Criar alteração de e-mail com validação.

### Sprint 6 — Categorias

- [ ] Criar model Category.
- [ ] Criar categorias iniciais.
- [ ] Criar listagem.
- [ ] Criar criação e edição.
- [ ] Validar unicidade case-insensitive.
- [ ] Criar exclusão segura.
- [ ] Aplicar tokens de cor.
- [ ] Filtrar por workspace.

### Sprint 7 — Onboarding

- [ ] Criar rota e controle de acesso.
- [ ] Criar etapa nome.
- [ ] Criar etapa áreas.
- [ ] Criar etapa foco padrão.
- [ ] Criar etapa primeira tarefa.
- [ ] Criar etapa rotina opcional.
- [ ] Persistir progresso.
- [ ] Implementar pular.
- [ ] Marcar conclusão.
- [ ] Evitar repetição.
- [ ] Criar tela final.

### Sprint 8 — Model de tarefas

- [ ] Criar Task.
- [ ] Criar choices de status e prioridade.
- [ ] Criar constraints e índices.
- [ ] Criar migration.
- [ ] Criar forms tenant-aware.
- [ ] Criar service de conclusão.
- [ ] Criar service de reabertura.
- [ ] Criar validação de categoria.
- [ ] Criar admin filtrado.

### Sprint 9 — Interface de tarefas

- [ ] Criar Caixa de entrada.
- [ ] Criar Hoje.
- [ ] Criar Esta semana.
- [ ] Criar Concluídas.
- [ ] Reusar mesma query base.
- [ ] Criar criação rápida.
- [ ] Criar edição.
- [ ] Criar exclusão com confirmação.
- [ ] Criar concluir/reabrir.
- [ ] Criar planejar para hoje.
- [ ] Criar mover para data.
- [ ] Criar filtros.
- [ ] Criar paginação.
- [ ] Preservar query params.
- [ ] Criar empty states.

### Sprint 10 — Rotina semanal

- [ ] Criar WeeklyRoutineItem.
- [ ] Validar weekdays.
- [ ] Criar RoutineOccurrence.
- [ ] Criar snapshots.
- [ ] Criar constraints.
- [ ] Criar página semanal.
- [ ] Criar item.
- [ ] Editar item.
- [ ] Pausar/reativar.
- [ ] Excluir com histórico protegido.
- [ ] Criar command de geração.
- [ ] Garantir idempotência.

### Sprint 11 — Execução da rotina

- [ ] Gerar ocorrências do dia.
- [ ] Exibir na Home.
- [ ] Concluir ocorrência.
- [ ] Pular ocorrência.
- [ ] Impedir alteração de histórico.
- [ ] Criar fallback de geração no acesso.
- [ ] Criar histórico básico.
- [ ] Validar timezone.

### Sprint 12 — Motor de foco

- [ ] Criar FocusSession.
- [ ] Criar constraints de relacionamento.
- [ ] Criar service de start.
- [ ] Impedir duas sessões ativas.
- [ ] Criar pause.
- [ ] Criar resume.
- [ ] Criar complete.
- [ ] Criar cancel.
- [ ] Calcular tempo por timestamps.
- [ ] Usar transações e locks.
- [ ] Criar recuperação após refresh.

### Sprint 13 — Interface imersiva

- [ ] Criar seletor de tarefa/rotina.
- [ ] Criar durações predefinidas.
- [ ] Criar duração personalizada.
- [ ] Criar modal/tela imersiva.
- [ ] Criar countdown no cliente.
- [ ] Sincronizar com backend.
- [ ] Criar pause/resume.
- [ ] Criar finalizar.
- [ ] Criar cancelar.
- [ ] Implementar som opcional.
- [ ] Implementar acessibilidade.

### Sprint 14 — Estatísticas de foco

- [ ] Criar selectors diários.
- [ ] Criar selectors semanais.
- [ ] Criar contagem de sessões.
- [ ] Criar tempo por categoria.
- [ ] Criar histórico paginado.
- [ ] Tratar sessões sem categoria.
- [ ] Validar arredondamento.
- [ ] Otimizar queries.

### Sprint 15 — Home

- [ ] Criar selector unificado da Home.
- [ ] Criar saudação e data.
- [ ] Mostrar até três tarefas.
- [ ] Mostrar rotina do dia.
- [ ] Criar CTA de foco.
- [ ] Mostrar tarefas concluídas.
- [ ] Mostrar minutos de foco.
- [ ] Criar dataset de sete dias.
- [ ] Implementar gráfico único.
- [ ] Criar cache tenant/user-aware.
- [ ] Criar estados vazios.
- [ ] Validar 1366×768.
- [ ] Validar 1440×900.
- [ ] Validar 1920×1080.
- [ ] Validar mobile com scroll.

### Sprint 16 — Notas

- [ ] Criar Note.
- [ ] Escolher formato do editor.
- [ ] Sanitizar conteúdo.
- [ ] Gerar plain_text.
- [ ] Criar lista.
- [ ] Criar editor.
- [ ] Criar exclusão.
- [ ] Criar busca.
- [ ] Criar debounce.
- [ ] Criar pin/unpin.
- [ ] Ordenar notas.
- [ ] Paginar quando necessário.

### Sprint 17 — Notificações

- [ ] Criar Notification.
- [ ] Criar service de notificação.
- [ ] Criar menu no header.
- [ ] Criar contador.
- [ ] Criar página/lista.
- [ ] Marcar como lida.
- [ ] Marcar todas.
- [ ] Validar URLs internas.
- [ ] Implementar polling leve.
- [ ] Filtrar por usuário e workspace.

### Sprint 18 — E-mail

- [ ] Configurar console backend.
- [ ] Configurar SMTP por env.
- [ ] Criar templates base.
- [ ] Testar recuperação de senha manualmente.
- [ ] Enfileirar e-mails não críticos.
- [ ] Usar `transaction.on_commit`.
- [ ] Tratar falhas de SMTP.
- [ ] Evitar vazamento de credenciais.

### Sprint 19 — Celery, RabbitMQ e Redis

- [ ] Configurar `core/celery.py`.
- [ ] Importar app em `core/__init__.py`.
- [ ] Configurar RabbitMQ.
- [ ] Configurar Redis result backend.
- [ ] Configurar cache.
- [ ] Instalar django-celery-beat.
- [ ] Instalar django-celery-results.
- [ ] Instalar dj-celery-panel.
- [ ] Criar task diária de ocorrências.
- [ ] Criar retries adequados.
- [ ] Criar notificações de conclusão.
- [ ] Validar worker e beat.

### Sprint 20 — IA opcional

- [ ] Confirmar modelo disponível.
- [ ] Criar feature flag.
- [ ] Criar schemas Pydantic.
- [ ] Criar estado LangGraph.
- [ ] Criar node validate_input.
- [ ] Criar node extract_task_fields.
- [ ] Criar node validate_schema.
- [ ] Criar repair único.
- [ ] Criar task Celery.
- [ ] Criar rate limit.
- [ ] Criar UI de revisão.
- [ ] Não salvar automaticamente.
- [ ] Criar fallback manual.
- [ ] Registrar custo/latência sem conteúdo sensível.

### Sprint 21 — Docker local

- [ ] Criar Dockerfile Python slim.
- [ ] Instalar dependências de build.
- [ ] Copiar requirements antes do código.
- [ ] Criar entrypoint web.
- [ ] Criar worker entrypoint.
- [ ] Criar docker-compose.yml.
- [ ] Adicionar healthchecks.
- [ ] Adicionar volumes.
- [ ] Adicionar depends_on local.
- [ ] Validar rebuild limpo.
- [ ] Validar Windows/WSL quando aplicável.

### Sprint 22 — Settings de produção

- [ ] Configurar WhiteNoise.
- [ ] Configurar STATIC_ROOT.
- [ ] Configurar media protegida.
- [ ] Configurar SECURE_PROXY_SSL_HEADER.
- [ ] Configurar SECURE_SSL_REDIRECT.
- [ ] Isentar healthcheck.
- [ ] Configurar HSTS.
- [ ] Configurar cookies seguros.
- [ ] Configurar ALLOWED_HOSTS por lista.
- [ ] Configurar CSRF_TRUSTED_ORIGINS por lista.
- [ ] Criar helper para secret files.
- [ ] Revisar logs.

### Sprint 23 — Docker Swarm e Traefik

- [ ] Criar docker-stack.yml.
- [ ] Criar serviço Traefik.
- [ ] Configurar provider Swarm.
- [ ] Configurar DNS-01 Cloudflare.
- [ ] Configurar wildcard.
- [ ] Configurar dashboard com Basic Auth.
- [ ] Criar app com duas réplicas.
- [ ] Criar update start-first.
- [ ] Criar rollback automático.
- [ ] Criar healthchecks.
- [ ] Criar restart policies.
- [ ] Criar limits/reservations.
- [ ] Criar redes pública/interna/egress.
- [ ] Garantir Celery fora da pública.
- [ ] Criar volumes.
- [ ] Configurar secrets.

### Sprint 24 — Deploy scripts

- [ ] Criar parser seguro de `.env`.
- [ ] Criar modo `--check-only`.
- [ ] Criar modo `--skip-build`.
- [ ] Validar Swarm.
- [ ] Validar secrets.
- [ ] Validar redes.
- [ ] Validar DEBUG.
- [ ] Validar ALLOWED_HOSTS.
- [ ] Validar placeholders.
- [ ] Fazer git pull.
- [ ] Buildar tags SHA/latest.
- [ ] Fazer login/push GHCR.
- [ ] Executar stack deploy.
- [ ] Forçar rollout.
- [ ] Imprimir status e comandos úteis.

### Sprint 25 — Backup, restore e smoke

- [ ] Criar backup PostgreSQL.
- [ ] Criar backup de media.
- [ ] Criar checksums.
- [ ] Criar rotação.
- [ ] Criar restore com confirmação.
- [ ] Criar smoke_check.sh.
- [ ] Validar healthcheck.
- [ ] Validar login.
- [ ] Validar static.
- [ ] Validar dependências.
- [ ] Ensaiar restauração em ambiente separado.
- [ ] Documentar RPO/RTO inicial.

### Sprint 26 — MKDocs

- [ ] Criar `mkdocs.yml`.
- [ ] Configurar Material.
- [ ] Configurar Mermaid.
- [ ] Documentar setup local.
- [ ] Documentar arquitetura.
- [ ] Documentar tenant.
- [ ] Documentar domínio.
- [ ] Documentar Celery.
- [ ] Documentar deploy.
- [ ] Documentar backup/restore.
- [ ] Documentar troubleshooting.
- [ ] Verificar links.

### Sprint 27 — Seed e demonstração

- [ ] Criar command `seed_demo`.
- [ ] Criar usuário demo.
- [ ] Criar workspace demo.
- [ ] Criar categorias.
- [ ] Criar tarefas em cenários variados.
- [ ] Criar rotinas.
- [ ] Criar ocorrências.
- [ ] Criar sessões em sete dias.
- [ ] Criar notas.
- [ ] Criar notificações.
- [ ] Garantir idempotência.
- [ ] Documentar credenciais somente para dev.

### Sprint 28 — Revisão de segurança

- [ ] Revisar todos os `get_queryset`.
- [ ] Revisar object lookups.
- [ ] Revisar forms e related fields.
- [ ] Revisar tasks Celery.
- [ ] Revisar redirects.
- [ ] Revisar CSRF.
- [ ] Revisar secrets.
- [ ] Revisar logs.
- [ ] Revisar admin.
- [ ] Revisar headers.
- [ ] Revisar uploads futuros.
- [ ] Executar cenários manuais cross-tenant.

### Sprint 29 — QA manual e lançamento

- [ ] Executar critérios funcionais.
- [ ] Validar onboarding completo.
- [ ] Validar onboarding pulado.
- [ ] Validar tarefas atrasadas.
- [ ] Validar geração de rotina.
- [ ] Validar foco com refresh.
- [ ] Validar pausa longa.
- [ ] Validar cancelamento.
- [ ] Validar gráfico em virada de dia.
- [ ] Validar timezone.
- [ ] Validar temas.
- [ ] Validar teclado e foco.
- [ ] Validar mobile.
- [ ] Validar desktop sem scroll.
- [ ] Validar deploy start-first.
- [ ] Validar rollback.
- [ ] Validar backup.
- [ ] Validar certificado wildcard.
- [ ] Revisar documentação.
- [ ] Marcar versão 1.0.

---

## 47. Definition of Done

Uma tarefa só está concluída quando:

- [ ] atende ao PRD;
- [ ] respeita tenant;
- [ ] usa nomes técnicos em inglês;
- [ ] UI está em pt-BR;
- [ ] segue design system;
- [ ] possui estados vazio, loading e erro quando aplicável;
- [ ] funciona em desktop e mobile;
- [ ] não cria N+1 evidente;
- [ ] possui migration quando necessário;
- [ ] atualiza documentação relevante;
- [ ] atualiza requirements se necessário;
- [ ] não inclui secrets;
- [ ] passou pelos critérios manuais da feature;
- [ ] foi executada no Docker local;
- [ ] não quebra `/health/`.

---

## 48. Checklist de lançamento

- [ ] Nome, domínio e placeholders definidos.
- [ ] Design system aprovado.
- [ ] Fluxos principais completos.
- [ ] Home sem scroll em desktop de referência.
- [ ] Isolamento cross-tenant revisado.
- [ ] Celery worker e beat estáveis.
- [ ] Redis e RabbitMQ persistentes e saudáveis.
- [ ] E-mail de recuperação funcionando.
- [ ] `.env` de produção protegido.
- [ ] Secrets criados.
- [ ] GHCR privado/público configurado conforme estratégia.
- [ ] Traefik dashboard protegido.
- [ ] Certificado wildcard válido.
- [ ] Backups agendados.
- [ ] Restore ensaiado.
- [ ] Smoke check aprovado.
- [ ] Logs sem dados sensíveis.
- [ ] Documentação publicada.
- [ ] Usuário administrador criado.
- [ ] Dados demo removidos ou isolados de produção.
- [ ] Feature de IA desligada até validação do modelo e custo.

---

## Considerações finais

O MVP deve priorizar clareza e execução. A arquitetura replica os padrões mais úteis do SCSI — modularidade Django, usuário por e-mail, isolamento multi-tenant, processamento assíncrono e deploy resiliente — mas adapta o domínio para workspaces de produtividade.

A ordem de implementação deve ser respeitada. Não iniciar IA, relatórios avançados ou integrações antes de autenticação, tenant, tarefas, rotina, foco e Home estarem estáveis.
