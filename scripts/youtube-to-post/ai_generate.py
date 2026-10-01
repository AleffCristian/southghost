import os
from pathlib import Path
import json
import re
from datetime import datetime

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
    texto = re.sub(r"\[Aplausos\]", " ", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\[risos\]", " ", texto, flags=re.IGNORECASE)
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

Transforme a transcrição fornecida em um artigo completo em português brasileiro.

O resultado NÃO deve parecer uma transcrição do vídeo.

O resultado deve parecer um artigo independente, organizado e bem editado, podendo assumir uma estrutura enciclopédica quando o assunto permitir.

Categoria: {categoria}

A transcrição fornecida é a fonte do conteúdo.

REGRAS SOBRE O CONTEÚDO:

- Preserve as informações, ideias, exemplos, nomes e explicações presentes na transcrição.
- Você pode reorganizar completamente a ordem das informações para melhorar a leitura.
- Você pode juntar trechos separados que tratam do mesmo assunto.
- Você pode eliminar repetições.
- Você pode transformar explicações faladas em texto escrito.
- Você pode transformar listas faladas em listas Markdown.
- Você pode criar subtítulos baseados nos assuntos realmente abordados.
- Você pode resumir trechos repetitivos sem perder informação relevante.
- Não escreva frases como "no vídeo", "o autor explica no vídeo", "como foi mencionado anteriormente no vídeo" ou equivalentes.
- Não escreva como se estivesse transcrevendo uma pessoa falando.
- Não preserve vícios de linguagem.
- Não preserve chamadas para inscrição, curtidas, comentários, doações ou encerramentos de vídeo.
- Remova marcas como [Música], [Aplausos] e [risos].
- Corrija erros evidentes de reconhecimento de voz somente quando o próprio contexto deixar a correção clara.
- Não invente informações.
- Não acrescente fatos externos apenas porque você conhece o assunto.
- Não invente datas, fontes, livros, autores, estatísticas ou acontecimentos.
- Não complete lacunas com conhecimento externo.
- Não faça pesquisa externa.
- Não transforme uma interpretação apresentada na transcrição em uma afirmação independente de fato.
- Quando a própria transcrição apresentar uma informação como possibilidade, tradição, crença, interpretação ou hipótese, preserve esse caráter.
- Não faça fact-checking.
- Não contradiga o conteúdo da transcrição usando conhecimento externo.

REGRAS DE ESTILO:

- Escreva como um artigo de referência ou enciclopédia.
- O texto pode ser detalhado.
- Priorize clareza e organização.
- Use linguagem natural em português brasileiro.
- Evite linguagem acadêmica desnecessariamente complicada.
- Evite frases genéricas.
- Evite introduções artificiais.
- Evite conclusões artificiais.
- Não tente convencer o leitor.
- Não use tom publicitário.
- Não use emojis.
- Não mencione inteligência artificial.
- Não diga que o texto foi gerado automaticamente.
- Não use primeira pessoa, a menos que seja indispensável para preservar uma informação específica da transcrição.
- Prefira terceira pessoa e construções impessoais.
- Use parágrafos de tamanho razoável.
- Não transforme cada frase em um parágrafo.
- Use H2 (`##`) para grandes assuntos.
- Use H3 (`###`) para subdivisões.
- Use listas Markdown quando houver enumerações.
- Não use H1 (`#`) no corpo do artigo. O Hugo já apresenta o título da página.

FORMATAÇÃO:

Retorne SOMENTE o Markdown completo.

O arquivo deve começar exatamente com:

---
title: "..."
description: "..."
draft: true
tags:
  - {categoria}
  - YouTube
---

Não coloque texto antes do front matter.

Não coloque uma seção "Fonte". O script adicionará essa seção automaticamente.

IMPORTANTE:

Não coloque Markdown escapado desnecessariamente.

Use:

## Título

e não:

**## Título**

Use:

*palavra*

para itálico.

Não transforme caracteres Markdown em sequências como \\*, \\( ou \\).

Links devem seguir o formato normal:

[Texto](https://exemplo.com)

e não devem conter barras invertidas antes dos caracteres Markdown.

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
    """
    Corrige problemas estruturais do Markdown antes de salvar o post.
    Essa etapa não utiliza a API.
    """

    linhas = markdown.splitlines()

    if not linhas or linhas[0].strip() != "---":
        print("[ERRO] Markdown sem front matter válido.")
        raise SystemExit(1)

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

    # Corrige Markdown escapado desnecessariamente.
    corpo = [
        linha
        .replace(r"\(", "(")
        .replace(r"\)", ")")
        .replace(r"\[", "[")
        .replace(r"\]", "]")
        for linha in corpo
    ]

    # Corrige títulos que tenham sido envolvidos em negrito.
    corpo_corrigido = []

    for linha in corpo:
        linha = re.sub(
            r"^\*\*(#{2,3})\s+(.+?)\*\*$",
            r"\1 \2",
            linha.strip(),
        )

        corpo_corrigido.append(linha)

    corpo = corpo_corrigido

    # Corrige itálico duplicado ou escapado.
    corpo = [
        linha.replace(r"\*", "*")
        for linha in corpo
    ]

    # Garante que o front matter tenha uma data.
    if not any(linha.startswith("date:") for linha in front_matter):
        data = datetime.now().astimezone().isoformat(timespec="seconds")

        indice_descricao = next(
            (
                i
                for i, linha in enumerate(front_matter)
                if linha.startswith("description:")
            ),
            1,
        )

        front_matter.insert(
            indice_descricao + 1,
            f"date: {data}",
        )

    # Descobre o título do front matter.
    titulo = None

    for linha in front_matter:
        if linha.startswith("title:"):
            titulo = (
                linha[len("title:"):]
                .strip()
                .strip('"')
            )
            break

    # Remove espaços vazios no início.
    while corpo and not corpo[0].strip():
        corpo.pop(0)

    # Remove H1 duplicado.
    if titulo and corpo:
        primeira_linha = corpo[0].strip()

        if primeira_linha.startswith("# "):
            h1 = primeira_linha[2:].strip()

            if h1 == titulo:
                corpo = corpo[1:]

    # Remove espaços vazios novamente.
    while corpo and not corpo[0].strip():
        corpo.pop(0)

    # Remove uma possível seção Fonte criada pela IA.
    indice_fonte = None

    for indice, linha in enumerate(corpo):
        if linha.strip().lower() in {
            "## fonte",
            "### fonte",
        }:
            indice_fonte = indice
            break

    if indice_fonte is not None:
        corpo = corpo[:indice_fonte]

        while corpo and not corpo[-1].strip():
            corpo.pop()

    # Adiciona a fonte de forma determinística.
    corpo.extend(
        [
            "",
            "## Fonte",
            "",
            f"[Vídeo no YouTube]({entrada['url']})",
            "",
        ]
    )

    return "\n".join(
        front_matter + [""] + corpo
    ).strip()


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

    # Nunca sobrescreve um artigo existente.
    # Também evita gastar créditos desnecessariamente.
    if output_file.exists():
        print(f"[ERRO] O post já existe: {output_file}")
        print("O script não sobrescreve posts existentes.")
        raise SystemExit(1)

    transcript_file = TRANSCRIPT_DIR / f"{video_id}.txt"

    if not transcript_file.exists():
        print(
            f"[ERRO] Transcrição não encontrada: {transcript_file}"
        )
        print(
            "Execute primeiro: "
            "python scripts/youtube-to-post/transcribe.py"
        )
        raise SystemExit(1)

    transcricao = limpar_transcricao(
        transcript_file.read_text(
            encoding="utf-8"
        )
    )

    if not transcricao:
        print("[ERRO] A transcrição está vazia.")
        raise SystemExit(1)

    if len(transcricao) > MAX_TRANSCRIPT_CHARS:
        print(
            f"[ERRO] Transcrição muito grande: "
            f"{len(transcricao)} caracteres."
        )
        print(
            f"Limite configurado: "
            f"{MAX_TRANSCRIPT_CHARS} caracteres."
        )
        raise SystemExit(1)

    print(f"[INFO] Modelo: {MODEL}")
    print(
        f"[INFO] Transcrição: "
        f"{len(transcricao)} caracteres"
    )
    print("[INFO] Enviando conteúdo para a OpenAI...")

    markdown = gerar_artigo(
        entrada,
        transcricao,
    )

    markdown = normalizar_markdown(
        markdown,
        entrada,
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file.write_text(
        markdown + "\n",
        encoding="utf-8",
    )

    print("[OK] Artigo gerado pela OpenAI.")
    print(f"[OK] Arquivo: {output_file}")
    print(
        f"[OK] Tamanho: "
        f"{len(markdown)} caracteres"
    )


if __name__ == "__main__":
    main()