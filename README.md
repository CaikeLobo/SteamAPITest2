# Steam Top 100 Tags Analyzer

Aplicacao em Python que coleta os 100 jogos mais jogados da Steam, enriquece os dados com detalhes da loja, armazena tudo em SQLite e gera analises em CSV, JSON e grafico.

## O que o projeto faz

- coleta os 100 jogos mais jogados;
- busca detalhes de cada jogo;
- salva os dados no SQLite em `data/steam.db`;
- processa os dados com Pandas;
- calcula estatisticas de tags, generos, desenvolvedores e publicadoras;
- exporta `output/tags.csv` e `output/tags.json`;
- gera o grafico `output/tags.png`;
- registra logs em `logs/app.log`.

## Estrutura

```text
steamAPItest/
├── data/
├── logs/
├── models/
├── output/
├── services/
├── utils/
├── main.py
├── requirements.txt
└── README.md
```

## Como executar

1. Crie e ative o ambiente virtual.
2. Instale as dependencias:

```bash
pip install -r requirements.txt
```

3. Execute o projeto:

```bash
python main.py
```

## Observacoes

- O endpoint de ranking usa dados publicos da Steam Charts.
- Os detalhes dos jogos sao obtidos via `appdetails` da Steam Store.
- As tags sao extraidas da pagina publica da loja do jogo.
- Campos ausentes sao registrados em log e o processo continua.
