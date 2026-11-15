# Ferramentas do agente

Este documento explica como consultar os dados estruturados pelo módulo `sabor_agent` e executar a demonstração local. A interface é independente de modelo e framework.

## Fluxo de chamada

1. `get_tool_definitions()` retorna as definições JSON Schema das ferramentas.
2. O chamador escolhe uma ferramenta e fornece seus argumentos estruturados.
3. `dispatch_tool(nome, argumentos)` valida a chamada e executa a ferramenta.
4. Para resultados tabulares, use o formatador correspondente para gerar uma resposta em português.

O despacho recebe uma chamada estruturada; ele não interpreta mensagens em linguagem natural nem decide a alocação de pedidos.

## Ferramentas disponíveis

| Nome | Argumentos obrigatórios | Uso |
|---|---|---|
| `get_producer_summary` | `producer_id`, `start_date`, `end_date` | Vendas e pagamentos do produtor no período inclusivo, com datas `AAAA-MM-DD`; usa o nome cadastrado quando disponível e mantém o ID como referência. |
| `lookup_price` | `product_query` | Preços da tabela de outubro de 2026. Retorna `matches` exatos e `suggestions` de variantes sem escolher uma. |
| `lookup_lot` | `lot_id` | Campos disponíveis para o lote; retorna `None` quando não encontrado. |

As três consultas estruturadas usam os CSVs locais. Preços e pagamentos são devolvidos conforme os dados, sem calcular descontos nem classificar pendências como atrasadas. As respostas de lote não incluem nome ou CPF do produtor.

## Chamar as ferramentas em Python

```python
from sabor_agent import (
    dispatch_tool,
    format_lot_lookup,
    format_price_lookup,
    format_producer_summary,
    get_tool_definitions,
)

# Catálogo independente de provedor ou framework.
definitions = get_tool_definitions()

# Resumo financeiro.
summary = dispatch_tool(
    "get_producer_summary",
    {
        "producer_id": "P001",
        "start_date": "2026-09-01",
        "end_date": "2026-10-31",
    },
)
print(format_producer_summary(summary))

# Preço: variantes aparecem separadas para confirmação.
price = dispatch_tool("lookup_price", {"product_query": "goiaba paluma"})
print(format_price_lookup(price))

# Rastreabilidade por ID.
lot = dispatch_tool("lookup_lot", {"lot_id": "LOT-2026-0089"})
print(format_lot_lookup(lot))
```

`dispatch_tool` aceita também o argumento opcional `data_dir`, caso os CSVs estejam em outra pasta:

```python
summary = dispatch_tool(
    "get_producer_summary",
    {
        "producer_id": "P001",
        "start_date": "2026-09-01",
        "end_date": "2026-10-31",
    },
    data_dir="caminho/para/Facepe",
)
```

Argumentos ausentes, inesperados ou ferramenta desconhecida geram `ToolDispatchError`. Os erros de validação e de dados das consultas tabulares são definidos em `sabor_agent.data_tools`.

## Executar a demonstração local

Na raiz do repositório, rode:

```powershell
python -m scripts.demo_data_tools
```

O script chama as três ferramentas tabulares e imprime seus resultados em JSON. Os argumentos opcionais são `--producer`, `--start`, `--end`, `--product`, `--lot` e `--data-dir`. Para ver os valores padrão e a sintaxe:

```powershell
python -m scripts.demo_data_tools --help
```

Por padrão, os CSVs são lidos de `source/Facepe/`. `source/` é local e deve permanecer ignorada pelo Git; o conjunto de dados não é incluído no repositório. Se os CSVs não estiverem nessa pasta, passe outro caminho com `--data-dir`.

## Testes locais

Para executar os testes das consultas, despacho e formatadores:

```powershell
python -m pytest tests/test_data_tools.py tests/test_orchestrator.py tests/test_formatters.py -q
```
