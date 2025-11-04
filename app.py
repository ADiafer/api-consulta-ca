from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

def limpar_texto(texto):
    return re.sub(r'\s+', ' ', texto).strip() if texto else "Não encontrado"

def consultar_ca(numero_ca):
    if not numero_ca.isdigit():
        return {"erro": "CA deve ser um número"}, 400

   url = f"https://consultaca.com.br/{numero_ca}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return {"erro": "Site fora do ar ou CA inválido"}, 404

        soup = BeautifulSoup(response.text, 'html.parser')

        # Verifica se a página diz "não encontrado"
        if "não encontrado" in response.text.lower() or "erro" in response.text.lower():
            return {"erro": "CA não encontrado no sistema"}, 404

        dados = {"ca": numero_ca}

        # 1. Nome do EPI (h1 ou title)
        h1 = soup.find('h1')
        if h1 and "EPI" in h1.get_text():
            dados["nome_epi"] = limpar_texto(h1.get_text())
        else:
            title = soup.find('title')
            if title:
                dados["nome_epi"] = limpar_texto(title.get_text().split("|")[0])

        # 2. Fabricante (Razão Social)
        razao = soup.find(string=re.compile(r'Razão Social', re.I))
        if razao:
            texto = razao.parent.get_text() if razao.parent else ""
            dados["fabricante"] = limpar_texto(texto.split(":", 1)[-1])
        else:
            dados["fabricante"] = "Não encontrado"

        # 3. Situação
        situacao = soup.find(string=re.compile(r'Situação', re.I))
        if situacao:
            texto = situacao.parent.get_text() if situacao.parent else ""
            match = re.search(r'(APROVADO|VENCIDO|CANCELADO|SUSPENSO)', texto, re.I)
            dados["situacao"] = match.group(1).upper() if match else "DESCONHECIDA"
        else:
            dados["situacao"] = "Não encontrado"

        # 4. Validade
        validade = soup.find(string=re.compile(r'Validade', re.I))
        if validade:
            texto = validade.parent.get_text() if validade.parent else ""
            match = re.search(r'\d{2}/\d{2}/\d{4}', texto)
            dados["validade"] = match.group(0) if match else "Não encontrado"
        else:
            dados["validade"] = "Não encontrado"

        return dados, 200

    except requests.exceptions.Timeout:
        return {"erro": "Timeout: consulta muito lenta"}, 504
    except Exception as e:
        return {"erro": f"Erro interno: {str(e)}"}, 500


@app.route('/api/ca/<numero_ca>')
def api_ca(numero_ca):
    resultado, status = consultar_ca(numero_ca)
    return jsonify(resultado), status

@app.route('/')
def home():
    return """
    <h1>API Consulta CA - EPI</h1>
    <p><strong>Teste com CA válido:</strong></p>
    <ul>
      <li><a href="/api/ca/42150">/api/ca/42150</a> → Luva 3M</li>
      <li><a href="/api/ca/8681">/api/ca/8681</a> → Botina Marluvas</li>
    </ul>
    """

if __name__ == '__main__':
    app.run()
