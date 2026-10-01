from pathlib import Path
import json
import re
import sys

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    print("[ERRO] Dependência ausente: youtube-transcript-api")
    print("Instale com: pip install youtube-transcript-api")
    raise SystemExit(1)


ROOT_DIR = Path(__file__).resolve().parents[2]
INPUT_FILE = ROOT_DIR / "data" / "youtube-posts.json"
OUTPUT_DIR = ROOT_DIR / "tmp" / "youtube-transcripts"


def extrair_video_id(url):
    match = re.search(
        r"(?:v=|youtu\.be/|youtube\.com/(?:shorts|embed)/)([A-Za-z0-9_-]{11})",
        url,
    )
    return match.group(1) if match else None


def carregar_video():
    with INPUT_FILE.open("r", encoding="utf-8") as file:
        entradas = json.load(file)

    for entrada in entradas:
        if entrada.get("gerar") is True:
            return entrada

    return None


def obter_transcricao(video_id):
    api = YouTubeTranscriptApi()

    try:
        transcript = api.fetch(video_id, languages=["pt", "pt-BR", "en"])
        return transcript
    except Exception as error:
        print(f"[ERRO] Não foi possível obter a transcrição: {error}")
        raise SystemExit(1)


def salvar_transcricao(video_id, transcript):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_file = OUTPUT_DIR / f"{video_id}.txt"

    linhas = []
    for item in transcript:
        linhas.append(item.text.strip())

    texto = " ".join(linhas).strip()

    with output_file.open("w", encoding="utf-8") as file:
        file.write(texto + "\n")

    return output_file, len(texto)


def main():
    if not INPUT_FILE.exists():
        print(f"[ERRO] Arquivo não encontrado: {INPUT_FILE}")
        raise SystemExit(1)

    entrada = carregar_video()

    if not entrada:
        print("[INFO] Nenhum vídeo marcado com gerar: true")
        return

    video_id = extrair_video_id(entrada["url"])

    if not video_id:
        print("[ERRO] Não foi possível extrair o ID do vídeo.")
        raise SystemExit(1)

    print(f"[INFO] Vídeo: {video_id}")
    print("[INFO] Procurando transcrição...")

    transcript = obter_transcricao(video_id)
    output_file, caracteres = salvar_transcricao(video_id, transcript)

    print(f"[OK] Transcrição obtida.")
    print(f"[OK] Caracteres: {caracteres}")
    print(f"[OK] Arquivo: {output_file}")


if __name__ == "__main__":
    main()
