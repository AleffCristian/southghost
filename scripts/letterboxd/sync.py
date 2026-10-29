"""Sincroniza os filmes do Letterboxd para data/filmes.json.

Capa, nota, crítica e link vêm do RSS do Letterboxd. O título exibido no site
é o título brasileiro, escolhido nesta ordem:

1. data/titulos-br.json (correção manual, chave = slug do filme no Letterboxd);
2. TMDB em pt-BR, se a variável TMDB_TOKEN (token de leitura v4) ou
   TMDB_API_KEY (chave v3) estiver definida;
3. o título original do Letterboxd.

O título original fica salvo em "titulo_original".
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path


RSS_URL = "https://letterboxd.com/AleffCristian/rss/"
ROOT_DIR = Path(__file__).resolve().parents[2]
OUTPUT_FILE = ROOT_DIR / "data" / "filmes.json"
TITULOS_BR_FILE = ROOT_DIR / "data" / "titulos-br.json"

TMDB_API = "https://api.themoviedb.org/3"
TMDB_TOKEN = os.environ.get("TMDB_TOKEN", "").strip()
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "").strip()

NAMESPACES = {
    "letterboxd": "https://letterboxd.com",
}


class DescriptionParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.poster = None

    def handle_starttag(self, tag, attrs):
        if tag != "img" or self.poster:
            return

        atributos = dict(attrs)
        self.poster = atributos.get("src")

    def handle_data(self, data):
        texto = data.strip()

        if texto:
            self.parts.append(texto)

    def get_review(self):
        return " ".join(self.parts)


def processar_descricao(html):
    parser = DescriptionParser()
    parser.feed(html)

    return parser.get_review(), parser.poster


def buscar_rss():
    request = urllib.request.Request(
        RSS_URL,
        headers={
            "User-Agent": "Mozilla/5.0",
        },
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def classificar_filme(nota):
    if nota is None:
        return None

    if nota <= 2.0:
        return "lixo"

    if nota <= 3.5:
        return "existe"

    return "top"


def slug_do_link(link):
    """https://letterboxd.com/usuario/film/fight-club/1/ -> fight-club"""
    if not link or "/film/" not in link:
        return None

    return link.split("/film/", 1)[1].strip("/").split("/")[0] or None


def tmdb_id_do_item(item):
    # O namespace do TMDB no RSS não é documentado; procura pelo nome local.
    for filho in item:
        if filho.tag.rsplit("}", 1)[-1] == "movieId" and (filho.text or "").strip():
            try:
                return int(filho.text.strip())
            except ValueError:
                return None

    return None


def processar_rss(xml_data):
    root = ET.fromstring(xml_data)
    filmes = []

    for item in root.findall("./channel/item"):
        titulo = item.findtext(
            "letterboxd:filmTitle",
            namespaces=NAMESPACES,
        )

        ano = item.findtext(
            "letterboxd:filmYear",
            namespaces=NAMESPACES,
        )

        nota = item.findtext(
            "letterboxd:memberRating",
            namespaces=NAMESPACES,
        )

        data_assistido = item.findtext(
            "letterboxd:watchedDate",
            namespaces=NAMESPACES,
        )

        link = item.findtext("link")
        descricao = item.findtext("description") or ""

        nota = float(nota) if nota else None
        review, poster = processar_descricao(descricao)

        filmes.append(
            {
                "titulo": titulo,
                "titulo_original": titulo,
                "ano": int(ano) if ano else None,
                "nota": nota,
                "categoria": classificar_filme(nota),
                "review": review,
                "data_assistido": data_assistido,
                "link": link,
                "poster": poster,
                "tmdb_id": tmdb_id_do_item(item),
            }
        )

    return filmes


def carregar_json(caminho, padrao):
    if not caminho.exists():
        return padrao

    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except json.JSONDecodeError as erro:
        print(f"Aviso: {caminho.name} inválido ({erro}); ignorando.")
        return padrao


def normalizar_existente(filme):
    """Arquivos antigos não tinham titulo_original: o título era o original."""
    filme.setdefault("titulo_original", filme.get("titulo"))
    filme.setdefault("tmdb_id", None)
    return filme


def mesclar_filmes(filmes_existentes, filmes_novos):
    filmes_por_link = {}

    for filme in filmes_existentes:
        link = filme.get("link")

        if link:
            filmes_por_link[link] = normalizar_existente(filme)

    for filme in filmes_novos:
        link = filme.get("link")

        if not link:
            continue

        anterior = filmes_por_link.get(link, {})

        # Reaproveita o título já traduzido pelo TMDB para não repetir a consulta.
        if anterior.get("titulo_fonte") == "tmdb":
            filme["titulo_tmdb"] = anterior.get("titulo")

        if not filme.get("tmdb_id"):
            filme["tmdb_id"] = anterior.get("tmdb_id")

        filmes_por_link[link] = filme

    filmes = list(filmes_por_link.values())

    filmes.sort(
        key=lambda filme: filme.get("data_assistido") or "",
        reverse=True,
    )

    return filmes


def tmdb_get(caminho, parametros):
    parametros = dict(parametros)
    headers = {"Accept": "application/json", "User-Agent": "southghost-sync"}

    if TMDB_TOKEN:
        headers["Authorization"] = f"Bearer {TMDB_TOKEN}"
    else:
        parametros["api_key"] = TMDB_API_KEY

    url = f"{TMDB_API}{caminho}?{urllib.parse.urlencode(parametros)}"
    request = urllib.request.Request(url, headers=headers)

    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read())


def titulo_tmdb(filme):
    """Título em pt-BR no TMDB, ou None se não achar."""
    if not (TMDB_TOKEN or TMDB_API_KEY):
        return None

    try:
        if filme.get("tmdb_id"):
            dados = tmdb_get(f"/movie/{filme['tmdb_id']}", {"language": "pt-BR"})
            return (dados.get("title") or "").strip() or None

        parametros = {"query": filme.get("titulo_original") or "", "language": "pt-BR"}

        if filme.get("ano"):
            parametros["year"] = filme["ano"]

        resultados = tmdb_get("/search/movie", parametros).get("results") or []

        if resultados:
            filme["tmdb_id"] = resultados[0].get("id")
            return (resultados[0].get("title") or "").strip() or None
    except (urllib.error.URLError, TimeoutError, ValueError) as erro:
        print(f"Aviso: TMDB falhou para {filme.get('titulo_original')!r}: {erro}")

    return None


def aplicar_titulos_br(filmes, titulos_manuais):
    contagem = {"manual": 0, "tmdb": 0, "original": 0}

    for filme in filmes:
        original = filme.get("titulo_original") or filme.get("titulo")
        filme["titulo_original"] = original
        slug = slug_do_link(filme.get("link"))

        titulo = None
        fonte = "original"

        if slug and titulos_manuais.get(slug):
            titulo, fonte = titulos_manuais[slug], "manual"
        else:
            ja_traduzido = filme.get("titulo") if filme.get("titulo_fonte") == "tmdb" else None
            titulo = filme.pop("titulo_tmdb", None) or ja_traduzido or titulo_tmdb(filme)

            if titulo:
                fonte = "tmdb"

        filme.pop("titulo_tmdb", None)
        filme["titulo"] = titulo or original
        filme["titulo_fonte"] = fonte
        contagem[fonte] += 1

    return contagem


def salvar_filmes(filmes):
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT_FILE.write_text(
        json.dumps(
            filmes,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main():
    filmes_existentes = carregar_json(OUTPUT_FILE, [])
    titulos_manuais = {
        chave: valor
        for chave, valor in carregar_json(TITULOS_BR_FILE, {}).items()
        if not chave.startswith("_") and isinstance(valor, str) and valor.strip()
    }

    # Se o Letterboxd estiver fora do ar, publica com os dados que já temos
    # em vez de derrubar o deploy do site inteiro.
    try:
        filmes_novos = processar_rss(buscar_rss())
    except (urllib.error.URLError, TimeoutError, ET.ParseError) as erro:
        print(f"Aviso: não foi possível ler o RSS do Letterboxd ({erro}). Mantendo os dados atuais.")
        filmes_novos = []

    filmes = mesclar_filmes(filmes_existentes, filmes_novos)
    contagem = aplicar_titulos_br(filmes, titulos_manuais)
    salvar_filmes(filmes)

    print(f"{len(filmes_novos)} filme(s) recebido(s) do RSS.")
    print(f"{len(filmes)} filme(s) mantido(s) no total.")
    print(
        "Títulos: "
        f"{contagem['manual']} manual, {contagem['tmdb']} TMDB, "
        f"{contagem['original']} original."
    )

    if not (TMDB_TOKEN or TMDB_API_KEY):
        print("TMDB desativado: defina TMDB_TOKEN ou TMDB_API_KEY para traduzir filmes novos.")


if __name__ == "__main__":
    sys.exit(main())
