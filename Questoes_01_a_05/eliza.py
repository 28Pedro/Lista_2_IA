"""Versão reduzida do ELIZA em português, seguindo o algoritmo de Weizenbaum (1966)."""
import re

SUBSTITUICOES = {
    "eu": "você", "estou": "está", "sou": "é", "tenho": "tem", "quero": "quer", "acho": "acha",
    "meu": "seu", "minha": "sua", "meus": "seus", "minhas": "suas", "me": "te", "comigo": "com você",
    "você": "eu",
}

# palavra-chave: (prioridade, [(decomposição, [remontagens])])
# na decomposição, * casa com qualquer sequência de palavras; na remontagem, (n) é o n-ésimo trecho casado
ROTEIRO = {
    "computador": (5, [("*", ["Computadores preocupam você?", "Por que você menciona computadores?"])]),
    "mãe": (3, [("*", ["Fale mais sobre a sua família.", "Quem mais na sua família vem à sua mente?"])]),
    "pai": (3, [("*", ["Fale mais sobre a sua família.", "Como é a relação com o seu pai?"])]),
    "quero": (2, [("* quer *", ["Por que você quer (2)?", "O que mudaria se você conseguisse (2)?"])]),
    "estou": (2, [("* está *", ["Há quanto tempo você está (2)?", "Por que você acha que está (2)?"])]),
    "você": (2, [("* eu * te *", ["O que faz você pensar que eu (2) te (3)?"]),
                 ("*", ["Estamos falando de você, não de mim."])]),
    "sempre": (1, [("*", ["Você consegue pensar em um exemplo específico?", "Sempre mesmo?"])]),
    "não": (0, [("*", ["Você está dizendo não só para ser negativo?", "Por que não?"])]),
    "sim": (0, [("*", ["Você parece ter certeza.", "Entendo."])]),
}

MEMORIA_CHAVE = ("meu", "minha", "meus", "minhas")
MEMORIA_REMONTAGEM = 'Antes você disse: "(0)". Isso tem relação com o que estamos conversando?'
PADRAO = ["Por favor, continue.", "Entendo. Fale mais sobre isso.", "O que isso significa para você?"]
DESPEDIDAS = {"tchau", "adeus"}


class Eliza:
    def __init__(self):
        self.memoria = []
        self.usos = {}
        self.rastro = {}

    def _proxima(self, chave, opcoes):
        i = self.usos.get(chave, 0)
        self.usos[chave] = i + 1
        return opcoes[i % len(opcoes)]

    def _casar(self, decomposicao, texto):
        regex = r"\s*".join("(.*?)" if p == "*" else re.escape(p) for p in decomposicao.split())
        m = re.match("^" + regex + "$", texto)
        return [g.strip() for g in m.groups()] if m else None

    def responder(self, entrada):
        palavras_todas = re.findall(r"[\wÀ-ÿ]+|[,.;!?]", entrada.lower())
        if DESPEDIDAS & set(palavras_todas):
            self.rastro = {"chave": "despedida"}
            return "Até logo. Obrigado por conversar comigo."

        # mantém apenas o primeiro trecho, separado por pontuação, que tenha palavra-chave
        trechos, atual = [], []
        for p in palavras_todas:
            if p in ",.;!?":
                trechos.append(atual)
                atual = []
            else:
                atual.append(p)
        trechos.append(atual)
        trecho = next((t for t in trechos if any(p in ROTEIRO or p in MEMORIA_CHAVE for p in t)), trechos[0])

        chaves = sorted((p for p in trecho if p in ROTEIRO), key=lambda p: -ROTEIRO[p][0])
        transformado = " ".join(SUBSTITUICOES.get(p, p) for p in trecho)

        if any(p in MEMORIA_CHAVE for p in trecho):
            m = re.search(r"\b(seu|sua|seus|suas)\b.*", transformado)
            if m:
                self.memoria.append(m.group(0))

        for chave in chaves:
            for decomposicao, remontagens in ROTEIRO[chave][1]:
                partes = self._casar(decomposicao, transformado)
                if partes is None:
                    continue
                modelo = self._proxima((chave, decomposicao), remontagens)
                resposta = re.sub(r"\((\d)\)", lambda g: partes[int(g.group(1)) - 1], modelo)
                self.rastro = {"chave": chave, "prioridade": ROTEIRO[chave][0], "transformado": transformado,
                               "decomposicao": decomposicao, "remontagem": modelo}
                return resposta

        if self.memoria:
            lembranca = self.memoria.pop(0)
            self.rastro = {"chave": "nenhuma (memória)", "transformado": transformado, "remontagem": MEMORIA_REMONTAGEM}
            return MEMORIA_REMONTAGEM.replace("(0)", lembranca)

        self.rastro = {"chave": "nenhuma (resposta padrão)", "transformado": transformado}
        return self._proxima("padrao", PADRAO)


if __name__ == "__main__":
    eliza = Eliza()
    print("ELIZA: Olá. Conte-me o que está incomodando você. (digite tchau para sair)")
    while True:
        fala = input("VOCÊ: ")
        print("ELIZA:", eliza.responder(fala))
        if eliza.rastro.get("chave") == "despedida":
            break
