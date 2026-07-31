# Breakpoints e Viewports

Este arquivo formaliza os breakpoints usados pelo design system e o contrato de layout da Home. Os valores seguem os breakpoints padrao usados no HTML de referencia, mas passam a ser uma decisao do ENGP e nao uma dependencia implicita do CDN do Tailwind.

## Breakpoints

| Nome | Largura minima | Uso principal |
|---|---:|---|
| base | 0px | mobile, formularios e uma coluna |
| sm | 640px | formularios em duas colunas e botoes lado a lado |
| md | 768px | grids de dois itens e navegacao auxiliar |
| lg | 1024px | shell com sidebar e Home desktop |
| xl | 1280px | navegacao completa e composicoes amplas |

O layout deve continuar fluido entre os pontos de corte. Breakpoints nao devem ser usados para criar uma versao paralela do mesmo componente.

## Viewports de referencia da Home

| Viewport | Header | Altura disponivel | Comportamento esperado |
|---|---:|---:|---|
| 1366 x 768 | 56px | 712px | sem scroll vertical em zoom 100% |
| 1440 x 900 | 56px | 844px | sem scroll vertical em zoom 100% |
| 1920 x 1080 | 56px | 1024px | sem scroll vertical em zoom 100% |

Em tablet, mobile, zoom ampliado ou altura menor que a referencia, o conteudo pode rolar. A ausencia de scroll no desktop nunca deve remover conteudo ou impedir zoom e teclado.

## Contrato de layout

```css
:root {
  --app-header-height: 3.5rem;
}

.app-shell {
  min-height: 100dvh;
}

.dashboard-main {
  min-height: calc(100dvh - var(--app-header-height));
}

@media (min-width: 1024px) and (min-height: 700px) {
  .dashboard-main {
    height: calc(100dvh - var(--app-header-height));
    overflow: hidden;
  }
}

@media (max-width: 1023px), (max-height: 699px) {
  .dashboard-main {
    height: auto;
    overflow: visible;
  }
}
```

## Regras de composicao

- Usar `minmax(0, 1fr)` em colunas que possam receber texto ou listas.
- Limitar a Home a tres tarefas e a uma quantidade compacta de ocorrencias.
- Usar `--layout-grid-gap` como gap base de 20px.
- Usar `--layout-desktop-gutter` como gutter de 64px apenas em larguras amplas.
- Reduzir gutters para 24px em mobile e 40px a partir de `sm`.
- Manter o botao de foco e os estados principais no primeiro viewport.
