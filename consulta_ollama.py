import os
from pathlib import Path
import git
from neo4j import GraphDatabase
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

# Configurações Neo4j
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Contexto fixo da Lei do Bem
contexto_base = """
A Lei do Bem (Lei nº 11.196/2005) oferece incentivos fiscais para empresas que realizam atividades de pesquisa e desenvolvimento (P&D) de inovação tecnológica no Brasil. Os principais objetivos são:

- Estimular a inovação tecnológica nas empresas.
- Incentivar o investimento privado em P&D.
- Tornar o país mais competitivo tecnologicamente.

Principais benefícios:

- Dedução de 20,4% a 34% do IRPJ e CSLL sobre gastos com P&D.
- Redução de 50% do IPI na compra de máquinas e equipamentos.
- Depreciação e amortização acelerada de bens utilizados em P&D.
- Isenção de IR na remessa ao exterior para registro de patentes.

As empresas devem estar em lucro real e cumprir os critérios legais para obter os incentivos.
"""

# Função para buscar contexto no grafo Neo4j
def buscar_contexto(termo):
    with driver.session() as session:
        query = """
        MATCH (b:Beneficio)
        WHERE toLower(b.descricao) CONTAINS toLower($termo)
        RETURN b.descricao AS beneficio
        LIMIT 5
        """
        resultados = session.run(query, termo=termo)
        contexto = [f"Benefício identificado: {row['beneficio']}" for row in resultados]

        if not contexto:
            query_fallback = """
            MATCH (b:Beneficio)
            RETURN b.descricao AS beneficio
            LIMIT 5
            """
            resultados = session.run(query_fallback)
            contexto = [f"Benefício identificado: {row['beneficio']}" for row in resultados]

        return "\n".join(contexto)

# Função para clonar repositório se não existir localmente
def clonar_repositorio(url: str, caminho_destino: str = "./repositorio"):
    if not os.path.exists(caminho_destino):
        print(f"Clonando repositório {url}...")
        git.Repo.clone_from(url, caminho_destino)
    else:
        print(f"Repositório já clonado em {caminho_destino}")

# Função para extrair conteúdo relevante de arquivos no repositório
def extrair_conteudo_relevante(caminho_destino: str = "./repositorio") -> str:
    extensoes_validas = (".py", ".md", ".txt", ".json", ".yaml", ".yml")
    palavras_chave = ["lei do bem", "incentivo fiscal", "p&d", "irpj", "csll", "inovação", "pesquisa e desenvolvimento"]
    conteudo = []

    for file in Path(caminho_destino).rglob("*"):
        if file.suffix.lower() in extensoes_validas:
            try:
                with open(file, "r", encoding="utf-8", errors="ignore") as f:
                    texto = f.read()
                    texto_lower = texto.lower()
                    if any(palavra in texto_lower for palavra in palavras_chave):
                        trecho = texto[:1000].strip()  # limitar tamanho
                        conteudo.append(f"Arquivo: {file.name}\n{trecho}")
            except Exception as e:
                print(f"Erro lendo {file}: {e}")

    # Retorna até 5 trechos encontrados
    return "\n\n".join(conteudo[:5]) if conteudo else "Nenhuma evidência relevante encontrada no repositório."

# Inicialização do LLM Ollama
llm = OllamaLLM(model="llama3")

# Template do prompt incluindo contexto base, grafo e repositório
prompt = PromptTemplate.from_template("""
Você é um especialista na Lei do Bem (Lei nº 11.196/2005). Responda com clareza e base legal à pergunta abaixo, usando os contextos fornecidos.

Contexto Fixo (lei e regras):
{contexto_base}

Contexto Dinâmico do Grafo:
{contexto_grafo}

Evidências encontradas no repositório de código:
{contexto_repo}

Pergunta:
{pergunta}

Resposta:
""")

# Função para responder com contexto completo
def responder(pergunta: str, repo_url: str = None) -> str:
    contexto_grafo = buscar_contexto(pergunta)

    contexto_repo = ""
    if repo_url:
        clonar_repositorio(repo_url)
        contexto_repo = extrair_conteudo_relevante()
    else:
        contexto_repo = "Nenhum repositório fornecido."

    resposta = (prompt | llm).invoke({
        "contexto_base": contexto_base,
        "contexto_grafo": contexto_grafo,
        "contexto_repo": contexto_repo,
        "pergunta": pergunta
    })
    return resposta

# Executa CLI simples
if __name__ == "__main__":
    pergunta = input("Digite sua pergunta sobre a Lei do Bem:\n>> ")
    url = input("Digite a URL do repositório para buscar evidências (ou deixe em branco para pular):\n>> ").strip()
    resposta = responder(pergunta, repo_url=url if url else None)
    print("\nResposta:\n", resposta)
