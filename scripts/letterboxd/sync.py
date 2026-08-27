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
        text = data.strip()

        if text:
            self.parts.append(text)

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
    xml_data = buscar_rss()
    filmes = processar_rss(xml_data)
    salvar_filmes(filmes)

    print(f"{len(filmes)} filme(s) sincronizado(s).")


if __name__ == "__main__":
    main()