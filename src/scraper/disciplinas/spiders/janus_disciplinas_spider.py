from pathlib import Path
from typing import Generator

from loguru import logger

from scrapy.http import FormRequest
from scrapy import Spider
from scrapy.http import Response, Request
from disciplinas.config.urls import (
    COMISSAO_POS_GRADUACAO_URL,
    BASE_URL,
)

class JanusDisciplinasSpider(Spider):
    name = "janus_disciplinas"

    start_urls = [BASE_URL]

    def parse(self, response: Response) -> Generator[FormRequest, None, None]:
        logger.debug(
            "Submetendo form para recuperar lista de comissões de pós-graduação"
        )
        post_url = COMISSAO_POS_GRADUACAO_URL

        yield FormRequest(
            url=post_url,
            formdata={"tipo": "T"},
            callback=self.parse_comissoes_pos_graduacao
        )

    def parse_comissoes_pos_graduacao(self, response: Response) -> Generator[Request, None, None]:
        """
        Lê a lista de comissões de pós-graduação e gera requisições para cada comissão.
        """
        logger.debug("Processando resultados da lista de comissões de pós-graduação")
        rows = response.css("table.dataTable.selecionavel > tr")
        if not rows:
            logger.warning("Nenhuma comissão de pós-graduação encontrada na resposta.")
            return

        for row in rows:
            codigo_comissao = row.css("td:nth-child(1)::text").get(default='').strip()

            nome_fragments = row.css("td:nth-child(2) a::text").getall()
            nome_comissao = ''.join(nome_fragments).strip()
            link = row.css("td:nth-child(2) a::attr(href)").get(default='')

            if not codigo_comissao and not nome_comissao:
                continue

            full_link = f'https://uspdigital.usp.br/janus/AreaListaPublico?codcpg={codigo_comissao}&tipo=T&'

            yield Request(
                url=full_link,
                callback=self.parse_comissao_page,
                cb_kwargs={
                    'codigo_comissao': codigo_comissao,
                    'nome_comissao': nome_comissao
                }
            )

        logger.debug(
            "Finalizado o processamento da lista de comissões de pós-graduação"
        )

    def parse_comissao_page(
        self,
        response: Response,
        codigo_comissao: str,
        nome_comissao: str
    ) -> Generator[Request, None, None]:
        """
        Lê a página de uma comissão de pós-graduação específica e extrai os dados.

        Digamos que queremos extrair os programas da comissão 'Faculdade de Direito',
        ela contém dois programas '2001 - Direito' e '2099 - Faculdade de Direito'
        que tem áreas de concentrações associadas como '2131 - Direito Civil' e
        '2499 - Faculdade de Direito', respectivamente.

        Só depois de extrair os links dessas áreas de concentração, podemos extrair as
        disciplinas associadas a cada área de concentração.
        """
        logger.debug(
            f"Processando página da comissão de pós-graduação: {codigo_comissao} "
            f"- {nome_comissao}"
        )

        tables = response.css("table.dataTable.selecionavel")

        for table in tables:
            codigo_programa, nome_programa = table.css("th::text").getall()

            rows = table.css("tr td a::text").getall()
            for row in rows:
                try:
                    codigo_area_concentracao, nome_area_concentracao = row.strip().split('-', 1)
                    codigo_area_concentracao = codigo_area_concentracao.strip()
                    nome_area_concentracao = nome_area_concentracao.strip()
                except Exception:
                    logger.error(
                        f"Erro ao separar código e nome da área de concentração: {row}"
                    )
                    continue

                logger.debug(f"""
                    Extraindo área de concentração:
                    Código do Programa: {codigo_programa}
                    Nome do Programa: {nome_programa}
                    Código da Área de Concentração: {codigo_area_concentracao}
                    Nome da Área de Concentração: {nome_area_concentracao}
                """)

                yield Request(
                    url=(
                        'https://uspdigital.usp.br/janus/TurmaLista?codcpg='
                        f'{codigo_comissao}&codare={codigo_area_concentracao}&'
                    ),
                    callback=self.parse_disciplinas,
                    cb_kwargs={
                        'codigo_comissao': codigo_comissao,
                        'nome_comissao': nome_comissao,
                        'codigo_programa': codigo_programa,
                        'nome_programa': nome_programa,
                        'codigo_area_concentracao': codigo_area_concentracao.strip(),
                        'nome_area_concentracao': nome_area_concentracao.strip(),
                    }
                )

    def parse_disciplinas(
        self,
        response: Response,
        codigo_comissao: str,
        nome_comissao: str,
        codigo_programa: str,
        nome_programa: str,
        codigo_area_concentracao: str,
        nome_area_concentracao: str
    ) -> Generator[Request, None, None]:
        """
        Extrai as disciplinas da área de concentração específica.
        """
        logger.debug(
            f"Extraindo disciplinas para a área de concentração: "
            f"{codigo_area_concentracao} - {nome_area_concentracao}"
        )

        table = response.css('table[width="95%"]')
        for row in table.css("tr[onclick]"):
            codigo_disciplina = row.css("td:nth-child(1) font::text").get(default='').strip()
            nome_disciplina = row.css("td:nth-child(2) font::text").get(default='').strip()
            ementa_url = row.css("td:nth-child(3) a::attr(href)").get(default='').strip()
            turma_url = row.css("td:nth-child(4) a::attr(href)").get(default='').strip()

            if not codigo_disciplina and not nome_disciplina:
                continue

            logger.info(f"""
                Disciplina Extraída:
                Código da Comissão: {codigo_comissao}
                Nome da Comissão: {nome_comissao}
                Código do Programa: {codigo_programa}
                Nome do Programa: {nome_programa}
                Código da Área de Concentração: {codigo_area_concentracao}
                Nome da Área de Concentração: {nome_area_concentracao}
                Código da Disciplina: {codigo_disciplina}
                Nome da Disciplina: {nome_disciplina},
                ementa_url: {ementa_url},
                turma_url: {turma_url}
            """)

            yield Request(
                    url=(
                        'https://uspdigital.usp.br/janus/Disciplina?sgldis='
                        f'{codigo_disciplina}&'
                    ),
                    callback=self.parse_ementa,
                    cb_kwargs={
                        'codigo_comissao': codigo_comissao,
                        'nome_comissao': nome_comissao,
                        'codigo_programa': codigo_programa,
                        'nome_programa': nome_programa,
                        'codigo_area_concentracao': codigo_area_concentracao,
                        'nome_area_concentracao': nome_area_concentracao,
                        'codigo_disciplina': codigo_disciplina,
                        'nome_disciplina': nome_disciplina,
                        'ementa_url': ementa_url,
                        'turma_url': turma_url
                    }
                )

    def _get_text_after_strong_label(self, response: Response, label_text: str) -> str:
        """
        Função auxiliar para pegar o texto de um <p class="...campoTextoMantendoLinhas">
        que vem logo após um <p> contendo um <strong> com o 'label_text'.
        """
        text_nodes = response.xpath(
            f"//strong[text() = '{label_text}']/parent::p/following-sibling::p"
            "[contains(@class, 'campoTextoMantendoLinhas')][1]//text()"
        ).getall()

        return "".join(text_nodes).strip()


    def parse_ementa(
        self,
        response: Response,
        codigo_comissao: str,
        nome_comissao: str,
        codigo_programa: str,
        nome_programa: str,
        codigo_area_concentracao: str,
        nome_area_concentracao: str,
        codigo_disciplina: str,
        nome_disciplina: str,
        ementa_url: str,
        turma_url: str
    ) -> Generator[dict, None, None]:
        """
        Extrai a ementa da disciplina.
        """
        ementa_criacao: str | None = None
        numero_creditos: int | None = None
        carga_horaria_teorica: int | None = None
        carga_horaria_pratica: int | None = None
        carga_horaria_estudo: int | None = None
        carga_horaria_duracao: str | None = None
        carga_horaria_total: str | None = None
        docentes_responsaveis: str | None = None
        ementa_objetivos: str | None = None
        ementa_justificativa: str | None = None
        ementa_conteudo: str | None = None
        ementa_forma_avaliacao: str | None = None
        ementa_bibliografia: str | None = None
        ementa_idiomas: str | None = None
        ementa_tipo_oferecimentos: str | None = None

        try:
            (
                ch_teorica,
                ch_pratica,
                ch_estudo,
                carga_horaria_duracao,
                _,
                carga_horaria_total,
                _
            ) = response.css("table.dataTable.selecionavel > tr td::text").getall()
        except Exception:
            logger.error(
                f"Erro ao extrair cargas horárias para a disciplina: "
                f"{codigo_disciplina} - {nome_disciplina}"
                f"foi extraido {response.css('table.dataTable.selecionavel > tr td::text').getall()}"
            )

        try:
            carga_horaria_teorica = int(ch_teorica.strip())
            carga_horaria_pratica = int(ch_pratica.strip())
            carga_horaria_estudo = int(ch_estudo.strip())
        except ValueError:
            carga_horaria_teorica = None
            carga_horaria_pratica = None
            carga_horaria_estudo = None

        p_elements = response.css("p.info.infopt")

        for p_element in p_elements:
            topico = p_element.css("strong::text").get(default='').strip()

            if topico == "Criação:":
                ementa_criacao = p_element.css("::text").get(default='').strip()
            elif topico == "Nº de Créditos:":
                numero_creditos_text = p_element.css("::text").get(default='').strip()
                try:
                    numero_creditos = int(numero_creditos_text)
                except ValueError:
                    numero_creditos = None

        docentes_nodes = response.xpath(
            "//strong[text() = 'Docentes Responsáveis:']/parent::p/following-sibling"
            "::p[@class='info' and not(strong)]"
        )
        docentes_responsaveis = ' | '.join([
            node.css('::text').get(default='').strip() for node in docentes_nodes
        ])

        ementa_idiomas = ' | '.join(
            response.xpath(
                "//strong[text() = 'Idiomas ministrados:']/parent::p/"
                "following-sibling::div/text()"
            ).getall()
        )
        ementa_conteudo = self._get_text_after_strong_label(response, "Conteúdo:")
        ementa_objetivos = self._get_text_after_strong_label(response, "Objetivos:")
        ementa_justificativa = self._get_text_after_strong_label(response, "Justificativa:")
        ementa_forma_avaliacao = self._get_text_after_strong_label(response, "Forma de Avaliação:")
        ementa_bibliografia = self._get_text_after_strong_label(response, "Bibliografia:")
        ementa_tipo_oferecimentos = self._get_text_after_strong_label(response, "Tipo de oferecimento da disciplina:")

        yield {
            'codigo': codigo_disciplina,
            'disciplina': nome_disciplina,
            'criacao': ementa_criacao,
            'n_creditos': numero_creditos,
            'carga_teorica': carga_horaria_teorica,
            'carga_pratica': carga_horaria_pratica,
            'carga_estudo': carga_horaria_estudo,
            'duracao': carga_horaria_duracao,
            'carga_total': carga_horaria_total, # adicionei essa fora da especificação
            'docentes_responsaveis': docentes_responsaveis,
            'objetivos': ementa_objetivos,
            'justificativa': ementa_justificativa,
            'avaliacao': ementa_forma_avaliacao,
            'conteudo': ementa_conteudo,
            'bibliografia': ementa_bibliografia,
            'idioma': ementa_idiomas,
            'oferecimento': ementa_tipo_oferecimentos,
        }
