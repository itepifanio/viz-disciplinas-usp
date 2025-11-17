"""
Read the scrapped data and preprocess its values.

If the scrapped data is available:
1. reads the JSON file
2. preprocess the data by adding filtering and data transformation
3. store the content in a pandas dataframe and return it
"""

from pathlib import Path

import pandas as pd

class DataReader:
    """Data scrapper reader and preprocessor."""

    def __init__(self, scrapped_data_path: Path, output_dataframe_path: Path):
        self._scrapped_data_path = scrapped_data_path
        self._output_dataframe_path = output_dataframe_path
        self._scrapped_data: pd.DataFrame | None = None
        self._output_dataframe: pd.DataFrame | None = None

        if scrapped_data_path.exists() is False:
            raise FileNotFoundError(
                f"Scrapped data file not found: {scrapped_data_path}"
            )

    @property
    def scrapped_data(self) -> pd.DataFrame:
        if self._scrapped_data is None:
            self._scrapped_data = pd.read_json(self._scrapped_data_path)

        return self._scrapped_data
    
    @property
    def dataframe(self) -> pd.DataFrame:
        """
        Get the preprocessed dataframe.
        
        If the file is available, it reads the preprocessed dataframe.
        Otherwise it preprocess the scrapped data and saves it to the output path.
        """
        # already cached
        if self._output_dataframe is not None:
            return self._output_dataframe
        
        if self._output_dataframe_path.exists():
            self._output_dataframe = pd.read_pickle(self._output_dataframe_path)
        else:
            df_preprocessed = self._preprocess(self.scrapped_data)
            df_preprocessed.to_pickle(self._output_dataframe_path)
            self._output_dataframe = df_preprocessed

        return self._output_dataframe

    def _extrair_carga_horaria(self, valor_texto: str | None) -> int:
        """
        Converte string de carga horária para número inteiro de horas.
        
        Recebe uma string como '120 horas' ou '15 semanas' e valor inteiro (em horas).
        """
        numero_str, tipo = str(valor_texto).split(' ')
        if tipo == 'horas':
            return int(numero_str)
        elif tipo == 'semanas':
            return 7 * 24 * int(numero_str)
        else:
            raise ValueError(f"Tipo desconhecido: {tipo}")

    def _preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """Read the scrapped data and preprocess its values."""
        # filtra disciplinas sem créditos atribuídos
        # use .loc[...] and .copy() to avoid SettingWithCopyWarning
        df = df.loc[~df['n_creditos'].isnull()].copy()

        # converte tipos de dados
        df.loc[:, 'criacao'] = pd.to_datetime(
            df['criacao'],
            format='%d/%m/%Y',
            errors='coerce'
        )
        for col in ('carga_teorica', 'carga_pratica', 'carga_estudo', 'n_creditos'):
            df.loc[:, col] = df[col].astype(int)

        df.loc[:, 'carga_total'] = df['carga_total'].apply(self._extrair_carga_horaria)
        df.loc[:, 'duracao'] = df['duracao'].apply(self._extrair_carga_horaria)
        df.loc[:, 'carga_total'] = df['carga_total'].astype(int)
        df.loc[:, 'duracao'] = df['duracao'].astype(int)

        return df
