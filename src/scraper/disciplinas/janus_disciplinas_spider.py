from pathlib import Path

from scrapy import Spider, Requests
from scraper.disciplinas.config.urls import COMISSAO_POS_GRADUACAO_URL

class JanusDisciplinasSpider(Spider):
    name = "janus_disciplinas"

    async def start(self) -> None:
        yield Request(
            url=COMISSAO_POS_GRADUACAO_URL,
            callback=self.parse
        )
