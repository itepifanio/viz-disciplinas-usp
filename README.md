# Viz Dsiciplinas USP

Esse projeto consiste no scrap das páginas das disciplinas da pós-graduação da USP e a
visualização dos dados.

```mermaid
graph TD
    %% Coleta de Dados
    subgraph Coleta["1. Coleta e Pré-processamento"]
        A[("Web Scraping: Sistema Janus (USP)")] -->|Python + Scrapy| B[Extração de Dados HTML]
        B --> C{Limpeza de Dados}
        C -- "Remover Corrompidos/Incompletos" --> D[DataFrame: 2213 Disciplinas]
    end

    %% Processamento NLP
    subgraph NLP["2. Processamento de Texto e Embeddings"]
        D -->|Pandas| E[Unificação de Colunas]
        E -- "Objetivos + Justificativa + Conteúdo" --> F[Texto Unificado]
        F -->|SBERT: all-mpnetbase-v2| G[Geração de Embeddings]
        G --> H[Redução de Dimensionalidade]
        H -- "UMAP & t-SNE" --> I[Coordenadas 2D]
    end

    %% Modelagem de Grafos
    subgraph Grafos["3. Modelagem de Redes"]
        D --> J[Grafo Semântico: Similaridade]
        D --> K[Grafo Bipartido: Docentes-Disciplinas]
        J & K -->|NetworkX| L[Estrutura de Grafos]
    end

    %% Visualização
    subgraph Viz["4. Visualização e Aplicação"]
        D & I & L --> M[Dashboard Streamlit]
        
        M --> N["Visualizações Interativas (Plotly)"]
        
        N --> O["Tree Map (Hierarquia de Programas)"]
        N --> P["Scatter Plot (Similaridade Temática)"]
        N --> Q["Grafos de Rede (Navegação Visual)"]
        N --> R["Stacked Bar & Doughnut (Créditos/Horas)"]
        N --> S["Nuvens de Palavras (Conteúdo)"]
        
        Q & R & S --> T[Planejador Acadêmico Interativo]
    end
```


## Instalação

- Crie um ambiente virtual python através do comando `python -m venv venv`
- Ative o ambiente através do comando `source venv/bin/activate`
- Instale as dependências via o comando `pip install -r requirements-dev.txt`

## Executando o projeto

- Acesse o diretório `cd src/scraper`
- Execute `scrapy crawl janus_disciplinas -o ../../nbs/output.json`

## Analisando os dados

- Execute `jupyter-lab` na raíz do projeto, um servidor irá inicializar
- Acesse o servidor através do seu browser e navegue até a pasta `nbs` para executar os
  notebooks

## Executando o streamlit app

A aplicação streamlit tem seus dados baixados, pre-processamentos executados antes de ser
ativada. Todos esses comportamentos são encapsulados via o seguinte comando:

```
python cli.py preview
```

## Debugando

Para desenvolver os scrapers é recomendado acessar a página do Janus via o seguinte comando:

```bash
scrapy shell https://uspdigital.usp.br/janus/componente/disciplinasOferecidasInicial.jsf -s USER_AGENT='Mozilla/5.0'
```

Isso irá abrir um shell do scrapy que permitirá o usuário trabalhar com o objeto response
da biblioteca, como [demonstrado na documentação](https://docs.scrapy.org/en/latest/intro/tutorial.html#following-links).
