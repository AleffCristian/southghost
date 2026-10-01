import os
from pathlib import Path
import json
import re

from openai import OpenAI


ROOT_DIR = Path(__file__).resolve().parents[2]
INPUT_FILE = ROOT_DIR / "data" / "youtube-posts.json"
TRANSCRIPT_DIR = ROOT_DIR / "tmp" / "youtube-transcripts"
OUTPUT_DIR = ROOT_DIR / "content" / "blog"

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
MAX_TRANSCRIPT_CHARS = 40000

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


def limpar_transcricao(texto):
    texto = re.sub(r"\[Música\]", " ", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def gerar_artigo(entrada, transcricao):
    categoria = CATEGORIAS.get(
        entrada["categoria"],
        entrada["categoria"].title(),
    )

    client = OpenAI()

    instrucoes = f"""
Você é o editor do SouthGhost.

Transforme a transcrição de um vídeo em um artigo para um blog pessoal em português brasileiro.

Categoria: {categoria}

Regras:
- Não invente fatos, fontes, acontecimentos ou informações que não estejam na transcrição.
- Preserve as ideias e informações apresentadas na transcrição.
- Remova vícios de linguagem, repetições, chamadas para inscrição, pedidos de like, pedidos de doação e trechos de encerramento do vídeo.
- Remova marcas como [Música].
- Corrija erros evidentes de transcrição e reconhecimento de voz quando o contexto permitir.
- Não escreva como uma transcrição.
- Organize o conteúdo em uma sequência lógica de leitura.
- Use títulos e subtítulos Markdown quando fizer sentido.
- Escreva de forma direta, clara e natural.
- Evite frases genéricas, introduções artificiais e linguagem típica de texto gerado por IA.
- Não use emojis.
- Não inclua referências externas que não estejam na transcrição.
- Não diga que o texto foi gerado por IA.
- Gere um título específico para o conteúdo, e não um título genérico.
- Gere uma descrição curta para o front matter.
- O resultado deve ser um arquivo Markdown compatível com Hugo.

Retorne SOMENTE o Markdown completo, começando pelo front matter YAML.

O front matter deve conter:
---
title: "..."
description: "..."
draft: true
tags:
  - {categoria}
  - YouTube
---

Depois do front matter, escreva o artigo.

Transcrição:
{transcricao}
"""

    response = client.responses.create(
        model=MODEL,
        input=instrucoes,
    )

    markdown = response.output_text.strip()

    if not markdown.startswith("---"):
        print("[ERRO] A API não retornou Markdown com front matter.")
        raise SystemExit(1)

    return markdown


def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("[ERRO] A variável OPENAI_API_KEY não está configurada.")
        print("PowerShell: $env:OPENAI_API_KEY='sua-chave'")
        raise SystemExit(1)

    entrada = carregar_video()
    video_id = extrair_video_id(entrada["url"])

    if not video_id:
        print("[ERRO] Não foi possível extrair o ID do vídeo.")
        raise SystemExit(1)

    output_file = OUTPUT_DIR / f"{entrada['slug']}.md"

    # Verifica antes da chamada à API para não gastar créditos
    # quando o arquivo de destino já existe.
    if output_file.exists():
        print(f"[ERRO] O post já existe: {output_file}")
        print("O script não sobrescreve posts existentes.")
        raise SystemExit(1)

    transcript_file = TRANSCRIPT_DIR / f"{video_id}.txt"

    if not transcript_file.exists():
        print(f"[ERRO] Transcrição não encontrada: {transcript_file}")
        print("Execute primeiro: python scripts/youtube-to-post/transcribe.py")
        raise SystemExit(1)

    transcricao = limpar_transcricao(
        transcript_file.read_text(encoding="utf-8")
    )

    if not transcricao:
        print("[ERRO] A transcrição está vazia.")
        raise SystemExit(1)

    if len(transcricao) > MAX_TRANSCRIPT_CHARS:
        print(
            f"[ERRO] Transcrição muito grande: {len(transcricao)} caracteres."
        )
        print(
            f"Limite configurado: {MAX_TRANSCRIPT_CHARS} caracteres."
        )
        raise SystemExit(1)

    print(f"[INFO] Modelo: {MODEL}")
    print(f"[INFO] Transcrição: {len(transcricao)} caracteres")
    print("[INFO] Enviando conteúdo para a OpenAI...")

    markdown = gerar_artigo(entrada, transcricao)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file.write_text(markdown + "\n", encoding="utf-8")

    print("[OK] Artigo gerado pela OpenAI.")
    print(f"[OK] Arquivo: {output_file}")
    print(f"[OK] Tamanho: {len(markdown)} caracteres")


if __name__ == "__main__":
    main()
