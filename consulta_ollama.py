import os
from neo4j import GraphDatabase
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

# Carrega variáveis de ambiente do .env
load_dotenv()

# Configurações do Neo4j via .env
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# 🌐 Contexto fixo sobre a Lei do Bem
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

# Função para buscar contexto adicional no grafo
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

        # Fallback: se não encontrar, retorna 5 aleatórios
        if not contexto:
            query_fallback = """
            MATCH (b:Beneficio)
            RETURN b.descricao AS beneficio
            LIMIT 5
            """
            resultados = session.run(query_fallback)
            contexto = [f"Benefício identificado: {row['beneficio']}" for row in resultados]

        return "\n".join(contexto)

# LLM local com Langchain + Ollama
llm = OllamaLLM(model="llama3")

# Template do prompt
prompt = PromptTemplate.from_template("""
Você é um especialista na Lei do Bem (Lei nº 11.196/2005). Responda com clareza e base legal à pergunta abaixo, usando o contexto fornecido.

Contexto Fixo:
{contexto_base}

Contexto Dinâmico do Grafo:
{contexto_grafo}

Pergunta:
{pergunta}

Resposta:
""")

# Função principal
def responder(pergunta: str) -> str:
    contexto_grafo = buscar_contexto(pergunta)
    resposta = (prompt | llm).invoke({
        "contexto_base": contexto_base,
        "contexto_grafo": contexto_grafo,
        "pergunta": pergunta
    })
    return resposta

# Execução principal
if __name__ == "__main__":
    pergunta = input(">> ")
    resposta = responder(pergunta)
    print("\nResposta:\n", resposta)
