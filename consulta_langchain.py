from langchain_community.llms.openrouter import OpenRouter
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import os

api_key = os.getenv("OPENROUTER_API_KEY")

llm = OpenRouter(api_key=api_key, model="gpt-4o-mini")

prompt = PromptTemplate.from_template("Pergunta: {pergunta}\nResposta:")

chain = LLMChain(llm=llm, prompt=prompt)

def responder(pergunta: str) -> str:
    return chain.invoke({"pergunta": pergunta})

if __name__ == "__main__":
    pergunta = "O que é a Lei do Bem?"
    print(responder(pergunta))
