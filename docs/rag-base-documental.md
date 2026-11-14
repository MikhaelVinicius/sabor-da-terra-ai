# RAG — Base Documental Sabor da Terra

## 1. Objetivo

Este módulo implementa o sistema de Retrieval-Augmented Generation (RAG) responsável pela consulta à base documental do projeto Sabor da Terra.

O módulo permite recuperar informações presentes em documentos relacionados a:

- certificações;
- contratos;
- fichas técnicas;
- inspeções e laudos;
- informações documentais de produtores.

O fluxo combina recuperação vetorial com geração de respostas utilizando Gemini, mantendo rastreabilidade das fontes utilizadas.

---

## 2. Arquitetura

O pipeline implementado segue o fluxo:

```text
Documentos
    ↓
Loader
    ↓
Sanitização
    ↓
Chunking
    ↓
Embeddings
    ↓
ChromaDB
    ↓
Retriever
    ↓
Prompt com contexto
    ↓
Gemini
    ↓
Resposta + fontes
```

Os documentos são carregados e sanitizados antes da indexação.

Depois, são divididos em chunks e transformados em embeddings utilizando o modelo:

```text
gemini-embedding-001
```

Os vetores são armazenados localmente no ChromaDB.

Durante uma consulta, a pergunta também é transformada em embedding. O retriever busca os chunks semanticamente mais relevantes e os envia como contexto para o modelo de geração.

---

## 3. Estrutura do módulo

```text
sabor_rag/
├── __init__.py
├── config.py
├── models.py
├── redaction.py
├── loader.py
├── chunking.py
├── embeddings.py
├── vector_store.py
├── indexer.py
├── retriever.py
├── prompting.py
├── generator.py
├── service.py
└── tool.py
```

### Responsabilidades

`config.py`

Configura caminhos, modelos, parâmetros de recuperação e variáveis de ambiente.

`models.py`

Define as estruturas utilizadas pelo pipeline, incluindo documentos, chunks, resultados de recuperação e citações.

`redaction.py`

Remove ou mascara informações sensíveis antes da indexação.

`loader.py`

Carrega documentos TXT e PDF e extrai metadados relevantes.

`chunking.py`

Divide documentos em trechos menores utilizados na indexação vetorial.

`embeddings.py`

Gera embeddings de documentos e consultas utilizando Gemini.

`vector_store.py`

Gerencia a base vetorial persistente utilizando ChromaDB.

`indexer.py`

Executa o processo de indexação dos documentos.

`retriever.py`

Realiza busca semântica e retorna os chunks mais relevantes.

`prompting.py`

Constrói o prompt utilizado para geração fundamentada nas fontes recuperadas.

`generator.py`

Realiza a chamada ao modelo Gemini responsável pela geração da resposta.

`service.py`

Orquestra retrieval, geração e extração das citações.

`tool.py`

Expõe a interface pública utilizada pelos demais módulos do sistema.

---

## 4. Base documental

A base utilizada pelo módulo está localizada em:

```text
data/documents/
```

Organizada em:

```text
data/documents/
├── certificacoes/
├── contratos/
└── fichas_tecnicas/
```

Atualmente a base contém 20 documentos:

```text
12 certificações/laudos/inspeções
3 contratos
5 fichas técnicas
```

O loader suporta:

```text
.txt
.pdf
```

---

## 5. Sanitização de dados

Antes da indexação, o módulo executa sanitização de informações sensíveis.

Entre os dados tratados estão:

- CPF;
- conta bancária;
- agência;
- chave PIX;
- telefone.

A sanitização ocorre antes da criação dos embeddings, evitando que esses dados sejam armazenados diretamente na base vetorial.

---

## 6. Chunking

Os documentos são divididos em chunks antes da geração dos embeddings.

Configuração padrão:

```text
max_chars = 1200
overlap_chars = 200
```

O overlap mantém parte do contexto entre chunks consecutivos.

Na base documental atual:

```text
20 documentos → 45 chunks
```

Cada chunk possui identificador próprio e mantém metadados como:

- documento de origem;
- caminho da fonte;
- categoria;
- índice do chunk;
- identificador do produtor, quando disponível.

---

## 7. Embeddings

Modelo utilizado:

```text
gemini-embedding-001
```

Os documentos utilizam:

```text
RETRIEVAL_DOCUMENT
```

As consultas utilizam:

```text
RETRIEVAL_QUERY
```

Os embeddings gerados possuem dimensão 3072.

---

## 8. Banco vetorial

O módulo utiliza ChromaDB com persistência local.

Diretório padrão:

```text
data/chroma/
```

Esse diretório não deve ser versionado no Git.

A similaridade utilizada pela coleção é:

```text
cosine
```

---

## 9. Retrieval

O retriever realiza busca semântica na coleção vetorial.

Configuração padrão:

```text
top_k = 5
min_score = 0.30
```

Os resultados abaixo do score mínimo são descartados.

---

## 10. Grounding

O modelo de geração recebe apenas os chunks recuperados como contexto documental.

O prompt contém regras para:

- utilizar somente as fontes fornecidas;
- não inventar informações;
- informar quando a base não contém a resposta;
- preservar estados documentais como vencida, expirada e em renovação;
- não interpretar renovação como certificação válida;
- informar divergências entre documentos;
- não revelar informações sanitizadas;
- citar as fontes utilizadas.

Quando não existe informação suficiente, a resposta esperada é:

```text
Informação não encontrada na base documental.
```

---

## 11. Caso crítico de validação

Um dos principais casos utilizados na validação é a certificação orgânica da produtora Josefa Alves de Souza, identificada como P008.

O sistema deve distinguir corretamente:

```text
certificação vencida
```

de:

```text
certificação em processo de renovação
```

O fato de existir um processo de renovação não significa que a certificação esteja atualmente válida.

Esse cenário faz parte do Golden Set utilizado nos testes do RAG.

---

## 12. Golden Set

O conjunto de avaliação está localizado em:

```text
data/golden_set/questions.json
```

Ele contém perguntas com:

- fonte esperada;
- documento esperado;
- fatos esperados;
- termos verificáveis;
- descrição do caso.

O Golden Set é utilizado apenas para avaliação.

Ele não limita as perguntas que podem ser feitas ao sistema.

---

## 13. Avaliação de retrieval

Para avaliar a recuperação documental:

```bash
python scripts/evaluate_retrieval.py
```

Métricas obtidas na base atual:

```text
Hit@1: 5/5 — 100%
Hit@3: 5/5 — 100%
Hit@5: 5/5 — 100%
```

Nos cinco casos avaliados, o documento esperado apareceu como primeiro resultado da recuperação.

---

## 14. Avaliação de citações e cobertura factual

Para executar:

```bash
python scripts/evaluate_groundedness.py
```

Resultado obtido:

```text
Casos totais: 5
Casos executados: 5
Falhas de infraestrutura: 0

Fonte esperada citada: 5/5
Taxa de citação correta: 100%

Fatos esperados encontrados: 17/17
Cobertura factual geral: 100%
```

A cobertura factual verifica a presença dos fatos essenciais definidos no Golden Set.

Essa métrica não deve ser interpretada como garantia absoluta contra qualquer possível alucinação. Ela representa a cobertura dos critérios factuais definidos para os casos de avaliação.

---

## 15. Testes automatizados

Para executar todos os testes:

```bash
python -m pytest tests/ -v
```

Resultado atual:

```text
22 passed
```

Os testes cobrem componentes como:

- carregamento documental;
- categorias;
- sanitização;
- chunking;
- preservação de informações críticas;
- construção do prompt;
- parsing de citações;
- cobertura factual;
- interface pública do módulo.

---

## 16. Configuração

As dependências estão definidas em:

```text
requirements.txt
```

Para instalar:

```bash
pip install -r requirements.txt
```

A configuração utiliza variáveis de ambiente.

Crie um `.env` local baseado em:

```text
.env.example
```

A chave da API deve ser definida como:

```text
GEMINI_API_KEY=<sua-chave>
```

Nunca versione o arquivo `.env` ou a chave da API.

---

## 17. Construção do índice

Para reconstruir a base vetorial:

```bash
python scripts/build_index.py
```

O script:

```text
carrega documentos
→ sanitiza
→ divide em chunks
→ gera embeddings
→ grava no ChromaDB
```

A reconstrução do índice realiza chamadas à API de embeddings.

---

## 18. Consulta pelo terminal

O projeto possui o script:

```text
scripts/ask.py
```

Ele pode ser utilizado para realizar consultas manuais ao RAG.

---

## 19. Interface para integração

Os demais módulos não precisam conhecer a implementação interna do RAG.

A interface pública está disponível em:

```python
from sabor_rag.tool import consultar_base_documental
```

Exemplo:

```python
resultado = consultar_base_documental(
    "Qual é a situação da certificação de Josefa?"
)
```

O retorno segue a estrutura:

```python
{
    "resposta": "...",
    "fontes": [
        {
            "arquivo": "...",
            "documento": "...",
            "trecho": "..."
        }
    ]
}
```

Isso permite que o orquestrador utilize o módulo como uma ferramenta independente.

---

## 20. Uso pelo orquestrador

Quando uma pergunta depender da base documental, o orquestrador pode chamar:

```python
from sabor_rag.tool import consultar_base_documental


resultado = consultar_base_documental(pergunta)
```

O módulo é responsável internamente por:

```text
pergunta
→ embedding
→ retrieval
→ seleção de contexto
→ geração
→ citações
→ resposta estruturada
```

O orquestrador recebe apenas o resultado final e suas fontes.

---

## 21. Limites do módulo

O RAG deve ser utilizado para informações presentes na base documental.

Dados estruturados pertencentes a outros módulos não devem ser artificialmente tratados pelo RAG.

Quando a informação não estiver disponível nos documentos, o módulo deve indicar ausência de informação em vez de inventar uma resposta.

---

## 22. Segurança e versionamento

Não devem ser enviados ao Git:

```text
.env
.venv/
data/chroma/
__pycache__/
*.pyc
.pytest_cache/
```

A chave Gemini deve permanecer apenas no ambiente local ou no sistema seguro de variáveis utilizado durante implantação.

---

## 23. Status

Estado atual do módulo:

```text
Loader                         OK
Sanitização                    OK
Chunking                       OK
Embeddings                     OK
ChromaDB                       OK
Indexação                      OK
Retriever                      OK
Prompting                      OK
Geração Gemini                 OK
Citações                       OK
Golden Set                     OK
Avaliação de retrieval         OK
Avaliação factual              OK
Interface pública              OK
Testes automatizados           22/22
```

Métricas atuais:

```text
Retrieval Hit@1:        100%
Retrieval Hit@3:        100%
Retrieval Hit@5:        100%
Citação correta:        100%
Cobertura factual:      100% (17/17)
```