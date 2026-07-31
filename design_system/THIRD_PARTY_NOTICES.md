# Avisos de terceiros

Auditoria inicial realizada em 2026-07-30. O escopo desta auditoria e o preview estatico em `design_system/design-system.html`. Nenhum item desta lista deve ser tratado como dependencia de runtime Django antes de ser fixado no `requirements.txt` ou no bundle correspondente.

## Dependencias usadas pelo preview

| Item | Versao/origem | Licenca | Decisao |
|---|---|---|---|
| Inter | Google Fonts, pesos 400 a 800 | SIL Open Font License 1.1 | Permitida; manter o aviso de licenca ao auto-hospedar a fonte. |
| Lucide | `lucide@0.462.0` via unpkg | ISC; icones derivados de Feather sob MIT | Biblioteca principal de icones. A versao esta fixada no HTML. |
| Tailwind Play CDN | `https://cdn.tailwindcss.com/` | MIT | Permitido somente no preview. Nao usar CDN dinamico no app ou em producao. |
| GSAP e ScrollTrigger | `3.12.2` via cdnjs | GSAP Standard No Charge License | Permitido para site e aplicacao web. Nao usar em ferramenta visual concorrente de Webflow. |

Fontes oficiais:

- Inter: https://github.com/rsms/inter/blob/master/LICENSE.txt
- Lucide: https://github.com/lucide-icons/lucide/blob/main/LICENSE
- Tailwind CSS: https://github.com/tailwindlabs/tailwindcss/blob/main/LICENSE
- GSAP: https://gsap.com/community/standard-license/

## Referencias importadas

`design_system/refs/fluxa/` contem arquivos capturados de uma referencia visual externa. A origem e os direitos de redistribuicao desses arquivos nao foram confirmados. Por isso, eles sao somente material de analise e nao podem ser importados pelo produto, copiados para templates ou publicados como assets do ENGP.

O bundle JavaScript e o arquivo de Iconify nessa pasta tambem sao referencias nao utilizadas pelo preview atual. O preview usa Lucide como biblioteca unica. Se algum asset de referencia for promovido para produto, a licenca especifica devera ser reavaliada antes da alteracao.

## Regras de distribuicao

- Manter este arquivo junto ao design system.
- Fixar versoes de scripts externos antes de promover o preview para uma pagina publicada.
- Preferir assets locais e verificaveis no app Django.
- Nao incluir imagens remotas de terceiros em componentes do produto sem origem e licenca registradas.
- Nao tratar uma licenca permissiva como autorizacao para reutilizar marca, textos ou dados da referencia Fluxa.
