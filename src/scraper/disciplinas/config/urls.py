"""
Módulo de configuração para URLs do scraper de disciplinas.

O scrap primeiro acessa a página com a lista da comissão da pós-graduação. Como cada
item da lista de comissões contém um link para a página com as áreas de concentração, o
próximo passo é acessar cada uma dessas páginas. Finalmente, de cada área de concentração,
são acessadas as páginas das disciplinas oferecidas, onde pode-se extrair os dados das
turmas oferecidas: docentes, idioma, forma de oferecimento (presencial, EAD, etc.),
horários, vagas, etc.

Exemplo de fluxo de URLs acessadas:
1. Página da comissão da pós-graduação (Faculdade de Direito)
2. Páginas das áreas de concentração (Direito Civil)
3. Páginas das disciplinas oferecidas (DCV5842 - Aspectos Fundamentais de Direito Civil)
"""

BASE_URL = "https://uspdigital.usp.br/janus/componente/disciplinasOferecidasInicial.jsf"

# Url depois de submeter o form que retorna a lista de comissões de pós-graduação
COMISSAO_POS_GRADUACAO_URL = "https://uspdigital.usp.br/janus/CPGLista"

AREAS_DE_CONCENTRACAO_URL_TEMPLATE = (
    "https://uspdigital.usp.br/janus/componente/disciplinasOferecidas.jsf"
    "?action=1&tipo=T&codcpg={codigo_comissao}"
)

DISCIPLINAS_OFERECIDAS_URL_TEMPLATE = (
    "https://uspdigital.usp.br/janus/componente/disciplinasOferecidas.jsf"
    "?action=2&tipo=T&codcpg={codigo_comissao}&codare={codigo_area_concentracao}"
)
