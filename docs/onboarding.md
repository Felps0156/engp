# Onboarding

## Fluxo

O onboarding é privado, exige uma membership ativa no workspace atual e usa
`/onboarding/` como ponto de entrada. O fluxo salva as etapas abaixo em
`OnboardingProgress`:

1. nome;
2. áreas principais;
3. duração padrão do foco;
4. primeira tarefa;
5. item opcional da rotina semanal.

O cadastro cria o progresso na mesma transação da conta, workspace,
membership, configurações e categorias padrão. O login e a área inicial
redirecionam usuários sem `onboarding_completed` para a etapa pendente.

## Persistência

`OnboardingProgress` é um registro por usuário com `current_step`,
`completed_steps` e `data`. A primeira tarefa e a rotina ficam identificadas
com `source: onboarding` até que os models de tarefas e rotina das próximas
sprints estejam disponíveis. Áreas customizadas são criadas no workspace de
forma idempotente e nomes existentes são reutilizados.

O botão “Pular por agora” usa POST e marca `UserSettings.onboarding_completed`
na mesma transação. A tela final permite a conclusão explícita e resume as
informações salvas.
