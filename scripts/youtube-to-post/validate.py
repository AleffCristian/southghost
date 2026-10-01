import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT_DIR = Path(__file__).resolve().parents[2]
INPUT_FILE = ROOT_DIR / "data" / "youtube-posts.json"

CATEGORIAS_VALIDAS = {
    "historia",
    "bode",
    "reflexivos",
    "goats",
}


def extrair_video_id(url):
    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"}:
        return None

    host = parsed.netloc.lower().split(":")[0]

    if host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [None])[0]

        if parsed.path.startswith("/shorts/"):
            return parsed.path.split("/")[2].split("/")[0]

        if parsed.path.startswith("/embed/"):
            return parsed.path.split("/")[2].split("/")[0]

    if host == "youtu.be":
        return parsed.path.strip("/").split("/")[0] or None

    return None


def validar_slug(slug):
    return bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug))


def validar_entrada(indice, entrada):
    erros = []

    if not isinstance(entrada, dict):
        return [f"entrada {indice}: deve ser um objeto JSON"]

    url = entrada.get("url", "").strip()
    slug = entrada.get("slug", "").strip()
    categoria = entrada.get("categoria", "").strip().lower()
    gerar = entrada.get("gerar")

    video_id = extrair_video_id(url)

    if not url:
        erros.append("URL ausente")
    elif not video_id:
        erros.append("URL do YouTube inválida ou formato não suportado")

    if not slug:
        erros.append("slug ausente")
    elif not validar_slug(slug):
        erros.append("slug inválido; use apenas letras minúsculas, números e hífens")

    if categoria not in CATEGORIAS_VALIDAS:
        erros.append(
            "categoria inválida; use: "
            + ", ".join(sorted(CATEGORIAS_VALIDAS))
        )

    if not isinstance(gerar, bool):
        erros.append("gerar deve ser true ou false")

    if erros:
        return erros

    print(f"[OK] entrada {indice}: {slug} ({video_id})")
    return []


def main():
    if not INPUT_FILE.exists():
        print(f"[ERRO] arquivo não encontrado: {INPUT_FILE}")
        raise SystemExit(1)

    try:
        with INPUT_FILE.open("r", encoding="utf-8") as file:
            entradas = json.load(file)
    except json.JSONDecodeError as error:
        print(f"[ERRO] JSON inválido: {error}")
        raise SystemExit(1)

    if not isinstance(entradas, list):
        print("[ERRO] youtube-posts.json deve conter uma lista")
        raise SystemExit(1)

    entradas_para_gerar = [
        (indice, entrada)
        for indice, entrada in enumerate(entradas, start=1)
        if isinstance(entrada, dict) and entrada.get("gerar") is True
    ]

    if not entradas_para_gerar:
        print("[INFO] Nenhuma entrada marcada com gerar: true")
        return

    total_erros = 0

    for indice, entrada in entradas_para_gerar:
        erros = validar_entrada(indice, entrada)

        for erro in erros:
            print(f"[ERRO] entrada {indice}: {erro}")

        total_erros += len(erros)

    if total_erros:
        print()
        print(f"Validação concluída com {total_erros} erro(s).")
        raise SystemExit(1)

    print()
    print(f"Validação concluída: {len(entradas_para_gerar)} vídeo(s) pronto(s).")


if __name__ == "__main__":
    main()
