from datetime import datetime
from pathlib import Path
import json
import re


ROOT_DIR = Path(__file__).resolve().parents[2]
INPUT_FILE = ROOT_DIR / "data" / "youtube-posts.json"
TRANSCRIPT_DIR = ROOT_DIR / "tmp" / "youtube-transcripts"
OUTPUT_DIR = ROOT_DIR / "content" / "blog"

CATEGORIAS = {
    "historia": "História",
    "bode": "É o Bode",
    "reflexivos": "Reflexivos",
    "goats": "GOATs",
}


def extrair_video_id(url):
    match = re.search(
        r"(?:v=|youtu\.be/|youtube\.com/(?:shorts|embed)/)([A-Za-z0-9_-]{11})",
        url,
    )
    return match.group(1) if match else None


def carregar_video():
    if not INPUT_FILE.exists():
        print(f"[ERRO] Arquivo não encontrado: {INPUT_FILE}")
        raise SystemExit(1)

    with INPUT_FILE.open("r", encoding="utf-8") as file:
        entradas = json.load(file)

    for entrada in entradas:
        if entrada.get("gerar") is True:
            return entrada

    print("[INFO] Nenhum vídeo marcado com gerar: true")
    raise SystemExit(0)


def titulo_do_slug(slug):
    palavras = re.split(r"[-_]+", slug.strip())
    return " ".join(palavra.capitalize() for palavra in palavras if palavra)


def quebrar_em_paragrafos(texto, tamanho=900):
    texto = re.sub(r"\s+", " ", texto).strip()

    if not texto:
        return []

    frases = re.split(r"(?<=[.!?])\s+", texto)
    paragrafos = []
    atual = []

    for frase in frases:
        atual.append(frase)

        if len(" ".join(atual)) >= tamanho:
            paragrafos.append(" ".join(atual).strip())
            atual = []

    if atual:
        paragrafos.append(" ".join(atual).strip())

    return paragrafos


def gerar_markdown(entrada, video_id, transcricao):
    slug = entrada["slug"]
    titulo = titulo_do_slug(slug)
    categoria = entrada["categoria"]
    categoria_nome = CATEGORIAS.get(categoria, categoria.title())
    data = datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")
    data = f"{data[:-2]}:{data[-2:]}"

    paragrafos = quebrar_em_paragrafos(transcricao)

    if not paragrafos:
        print("[ERRO] A transcrição está vazia.")
        raise SystemExit(1)

    conteudo = [
        "---",
        f'title: "{titulo}"',
        f"date: {data}",
        "draft: true",
        f'description: "Rascunho gerado a partir de uma transcrição do YouTube."',
        "tags:",
        f"  - {categoria_nome}",
        "  - YouTube",
        "---",
        "",
        f"# {titulo}",
        "",
        "> Rascunho gerado automaticamente a partir da transcrição do vídeo.",
        "",
    ]

    conteudo.extend(paragrafos)
    conteudo.extend(
        [
            "",
            "## Fonte",
            "",
            f"[Vídeo no YouTube]({entrada['url']})",
            "",
        ]
    )

    return "\n".join(conteudo)


def main():
    entrada = carregar_video()

    video_id = extrair_video_id(entrada["url"])
    if not video_id:
        print("[ERRO] Não foi possível extrair o ID do vídeo.")
        raise SystemExit(1)

    transcript_file = TRANSCRIPT_DIR / f"{video_id}.txt"

    if not transcript_file.exists():
        print(f"[ERRO] Transcrição não encontrada: {transcript_file}")
        print("Execute primeiro: python scripts/youtube-to-post/transcribe.py")
        raise SystemExit(1)

    transcricao = transcript_file.read_text(encoding="utf-8").strip()

    markdown = gerar_markdown(entrada, video_id, transcricao)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"{entrada['slug']}.md"

    if output_file.exists():
        print(f"[ERRO] O post já existe: {output_file}")
        print("O script não sobrescreve posts existentes.")
        raise SystemExit(1)

    output_file.write_text(markdown, encoding="utf-8")

    print("[OK] Post Markdown gerado.")
    print(f"[OK] Arquivo: {output_file}")
    print(f"[OK] Tamanho: {len(markdown)} caracteres")


if __name__ == "__main__":
    main()
