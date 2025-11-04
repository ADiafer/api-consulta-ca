from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

def limpar_texto(texto):
    return texto.strip() if texto else "Não informado"

def consultar_ca(numero_ca):
    url = f"http://consultaca.com/{numero_ca}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return {"erro": "CA não encontrado"}, 404

        soup = BeautifulSoup(response.text, 'html.parser')
        dados = {"ca": numero_ca}

        # Nome do EPI
        epi = soup.find('h1')
        dados["nome_epi"] = limpar_texto(epi.get_text()) if epi else "Não encontrado"

        # Fabricante
        razao = soup.find(string=re.compile(r'Razão Social', re.I))
        if razao and razao.parent:
            dados["fabricante"] = limpar_texto(razao.parent.get_text().split(":", 1)[-1])
        else:
            dados["fabricante"] = "Não encontrado"

        # Situação
        situacao = soup.find(string=re.compile(r'Situação', re.I))
        if situacao and situacao.parent:
            match = re.search(r'APROVADO|VENCIDO|CANCELADO', situacao.parent.get_text(), re.I)
            dados["situacao"] = match.group(0).upper() if match else "Não encontrado"
        else:
            dados["situacao"] = "Não encontrado"

        # Validade
        validade = soup.find(string=re.compile(r'Validade', re.I))
        if validade and validade.parent:
            match = re.search(r'\d{2}/\d{2}/\d{4}', validade.parent.get_text())
            dados["validade"] = match.group(0) if match else "Não encontrado"
        else:
            dados["validade"] = "Não encontrado"

        return dados, 200

    except:
        return {"erro": "Erro ao consultar"}, 500

@app.route('/api/ca/<numero_ca>')
def api_ca(numero_ca):
    resultado, status = consultar_ca(numero_ca)
    return jsonify(resultado), status

@app.route('/')
def home():
    return "<h1>API Consulta CA</h1><p>Use: /api/ca/8681</p>"

if __name__ == '__main__':
    app.run()
