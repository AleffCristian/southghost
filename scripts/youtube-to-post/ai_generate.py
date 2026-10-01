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

Sua tarefa é transformar a transcrição fornecida em um artigo para um blog pessoal em português brasileiro.

A transcrição é a ÚNICA fonte de conteúdo do artigo.

Categoria: {categoria}

REGRAS DE CONTEÚDO:
- Use exclusivamente informações, ideias, exemplos, nomes e interpretações presentes na transcrição.
- NÃO acrescente conhecimento externo, mesmo que você conheça o assunto.
- NÃO pesquise mentalmente ou complete lacunas com conhecimento próprio.
- NÃO introduza fatos históricos, religiosos, científicos ou culturais que não estejam na transcrição.
- NÃO transforme uma afirmação do narrador em um fato independente.
- Quando o narrador apresentar uma interpretação, preserve essa interpretação como interpretação.
- Quando uma informação estiver confusa ou incompleta, não invente uma explicação para completá-la. Se necessário, omita o trecho.
- Não faça fact-checking usando conhecimento externo.
- Não corrija uma informação factual do narrador com conhecimento externo. A tarefa aqui é edição, não pesquisa.
- Não invente fontes, citações, datas, estatísticas ou referências.
- Não crie exemplos que não aparecem na transcrição.

REGRAS DE EDIÇÃO:
- Remova vícios de linguagem, repetições e interrupções naturais da fala.
- Remova chamadas para inscrição, pedidos de like, pedidos de doação e encerramentos típicos de vídeo.
- Remova marcas como [Música].
- Corrija erros evidentes de transcrição e reconhecimento de voz somente quando o contexto da própria transcrição deixar a correção clara.
- Não escreva como uma transcrição.
- Organize as ideias em uma sequência lógica.
- Use títulos e subtítulos Markdown quando ajudarem a leitura.
- Preserve o sentido original.
- Não altere a posição ou o significado de uma opinião apresentada pelo narrador.
- Escreva em português brasileiro.
- Use frases claras e parágrafos de tamanho razoável.
- Evite frases genéricas, introduções artificiais, conclusões artificiais e linguagem típica de texto gerado por IA.
- Não use emojis.
- Não diga que o texto foi gerado por IA.
- Gere um título específico baseado no conteúdo real da transcrição.
- Gere uma descrição curta baseada somente no conteúdo da transcrição.
- NÃO repita o título como um cabeçalho H1 após o front matter. O Hugo já exibe o título da página.

FORMATO:
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

Não inclua uma seção "Fonte" no artigo. O script adicionará o link do vídeo automaticamente.

TRANSCRIÇÃO:
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


def normalizar_markdown(markdown, entrada):
    """Ajusta elementos que pertencem ao site e não ao texto gerado pela IA."""
    linhas = markdown.splitlines()

    if not linhas or linhas[0].strip() != "---":
        print("[ERRO] Markdown sem front matter válido.")
        raise SystemExit(1)

    # Encontra o fim do front matter YAML.
    fim_front_matter = None
    for indice in range(1, len(linhas)):
        if linhas[indice].strip() == "---":
            fim_front_matter = indice
            break

    if fim_front_matter is None:
        print("[ERRO] Front matter não foi encerrado corretamente.")
        raise SystemExit(1)

    front_matter = linhas[:fim_front_matter + 1]
    corpo = linhas[fim_front_matter + 1:]

    # A data deve ser definida pelo script, não pela IA.
    if not any(linha.startswith("date:") for linha in front_matter):
        from datetime import datetime
        data = datetime.now().astimezone().isoformat(timespec="seconds")
        insercao = next(
            (i for i, linha in enumerate(front_matter) if linha.startswith("description:")),
            1,
        )
        front_matter.insert(insercao + 1, f"date: {data}")

    # Remove um H1 inicial caso a IA tenha repetido o título apesar da instrução.
    titulo = None
    for linha in front_matter:
        if linha.startswith("title:"):
            titulo = linha[len("title:"):].strip().strip('"')
            break

    while corpo and not corpo[0].strip():
        corpo.pop(0)

    if titulo and corpo and corpo[0].strip().startswith("# "):
        h1 = corpo[0].strip()[2:].strip()
        if h1 == titulo:
            corpo = corpo[1:]

    while corpo and not corpo[0].strip():
        corpo.pop(0)

    # A fonte é adicionada de forma determinística pelo script.
    corpo.extend([
        "",
        "## Fonte",
        "",
        f"[Vídeo no YouTube]({entrada['url']})",
        "",
    ])

    return "\n".join(front_matter + [""] + corpo).strip()


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
    markdown = normalizar_markdown(markdown, entrada)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file.write_text(markdown + "\n", encoding="utf-8")

    print("[OK] Artigo gerado pela OpenAI.")
    print(f"[OK] Arquivo: {output_file}")
    print(f"[OK] Tamanho: {len(markdown)} caracteres")


if __name__ == "__main__":
    main()
