"""
Recupera a tabela de comissões de pós-graduação.
"""

from dataclasses import dataclass

from scrapy.http import Response

@dataclass
class ComissaoPosGraduacaoItem:
    """Representa um item da tabela de comissões de pós-graduação."""
    codigo: str
    nome: str

class ComissaoPosGraduacaoTable:
    """Representa a tabela de comissões de pós-graduação."""

    def __init__(self) -> None:
        self.items: list[ComissaoPosGraduacaoItem] = []

    def parse(self, response: Response) -> None:
        """Extrai os itens da tabela a partir da resposta HTTP."""
        pass
