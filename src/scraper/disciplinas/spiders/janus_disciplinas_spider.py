from pathlib import Path
from typing import Generator

from loguru import logger

from scrapy.http import FormRequest
from scrapy import Spider
from scrapy.http import Response
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
            callback=self.parse_results
        )

    def parse_results(self, response: Response) -> Generator[dict[str, str], None, None]:
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

            yield {
                'codigo': codigo_comissao,
                'nome': nome_comissao,
                'link': response.urljoin(link),
            }

        logger.debug(
            "Finalizado o processamento da lista de comissões de pós-graduação"
        )
