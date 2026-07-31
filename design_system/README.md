# ENGP Design System

## Identidade

- Produto: `ENGP`
- Descricao: sistema de produtividade pessoal
- Slug Python: `engp`
- Slug Docker: `engp`
- Imagem: `ghcr.io/Felps0156/engp`
- Dominio local: `engp.localhost`
- Dominio de producao: ainda depende de uma decisao operacional; nao usar o dominio local em producao.

O nome Fluxa e apenas a origem visual da referencia. A marca, textos, exemplos e assets da referencia nao fazem parte do produto ENGP.

## Fonte de verdade

- `design-system.html`: inventario visual e exemplos de componentes.
- `tokens.css`: cores, tipografia, espacamento, raios, sombras, motion e estados.
- `breakpoints.md`: breakpoints e contrato de viewport da Home.
- `THIRD_PARTY_NOTICES.md`: licencas, versoes e regras para referencias externas.

O app Django devera consumir os tokens em implementacoes reais, em vez de repetir valores arbitrarios por componente.

## Direcao visual

- Interface clara, com superficies brancas e slate.
- Azul como cor de acao e navy como cor de contraste forte.
- Inter como familia tipografica.
- Lucide como biblioteca unica de icones, com stroke padrao de 1.5 no preview.
- Bordas de 1px, sombras suaves e cards compactos.
- Movimento discreto, sempre respeitando `prefers-reduced-motion`.

## Escopo do preview

O HTML e um catalogo estatico. Ele nao e ainda o shell do produto, nao implementa autenticacao, dados, tema persistido ou componentes Django e nao deve ser interpretado como uma tela funcional.
