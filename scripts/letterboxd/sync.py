import json
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path


RSS_URL = "https://letterboxd.com/AleffCristian/rss/"
OUTPUT_FILE = Path(__file__).resolve().parents[2] / "data" / "filmes.json"

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
                "ano": int(ano) if ano else None,
                "nota": nota,
                "categoria": classificar_filme(nota),
                "review": review,
                "data_assistido": data_assistido,
                "link": link,
                "poster": poster,
            }
        )

    return filmes


def carregar_filmes_existentes():
    if not OUTPUT_FILE.exists():
        return []

    try:
        return json.loads(
            OUTPUT_FILE.read_text(encoding="utf-8")
        )
    except json.JSONDecodeError:
        return []


def mesclar_filmes(filmes_existentes, filmes_novos):
    filmes_por_link = {}

    for filme in filmes_existentes:
        link = filme.get("link")

        if link:
            filmes_por_link[link] = filme

    for filme in filmes_novos:
        link = filme.get("link")

        if not link:
            continue

        filmes_por_link[link] = filme

    filmes = list(filmes_por_link.values())

    filmes.sort(
        key=lambda filme: filme.get("data_assistido") or "",
        reverse=True,
    )

    return filmes


def salvar_filmes(filmes):
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT_FILE.write_text(
        json.dumps(
            filmes,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def main():
    filmes_existentes = carregar_filmes_existentes()
    xml_data = buscar_rss()
    filmes_novos = processar_rss(xml_data)

    filmes = mesclar_filmes(
        filmes_existentes,
        filmes_novos,
    )

    salvar_filmes(filmes)

    print(
        f"{len(filmes_novos)} filme(s) recebido(s) do RSS."
    )
    print(
        f"{len(filmes)} filme(s) mantido(s) no total."
    )


if __name__ == "__main__":
    main()