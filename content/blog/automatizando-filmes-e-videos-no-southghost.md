---
title: "Automatizando Filmes e Vídeos no SouthGhost"
date: 2026-08-28T11:18:00-03:00
description: "Como transformei Letterboxd e playlists do YouTube em dados consumidos automaticamente pelo Hugo."
tags:
  - Hugo
  - Python
  - Automação
  - Letterboxd
  - YouTube
featured: false
---

O SouthGhost começou como um blog estático.

A ideia continua sendo essa.

Não quero transformar um site feito em Hugo em uma aplicação cheia de dependências, banco de dados e serviços rodando só porque agora quero mostrar filmes e vídeos.

Mas eu também não queria cadastrar tudo manualmente.

Nas últimas alterações resolvi dois problemas parecidos:

- minhas avaliações do Letterboxd deveriam aparecer automaticamente no site;
- algumas playlists do YouTube deveriam virar uma biblioteca de vídeos dentro do SouthGhost.

A solução nos dois casos acabou seguindo praticamente a mesma arquitetura:

```text
serviço externo
      ↓
feed público
      ↓
Python
      ↓
JSON
      ↓
Hugo
      ↓
HTML estático
```

O navegador não consulta Letterboxd, não consulta YouTube.

O Hugo recebe dados já processados e gera HTML. Era exatamente o que eu queria.

---

## Letterboxd sem API

<!-- PRINT 01 -->
![Preservação do histórico de filmes](/imagens/posts/filmes-videos/filmes-historico.png)

A primeira ideia foi integrar o SouthGhost com o Letterboxd.

Eu queria avaliar normalmente um filme por lá e fazer o site aproveitar essa informação.

O problema é que eu não precisava e nem queria construir uma integração complexa para isso.

O Letterboxd já expõe um RSS público.

Então comecei por ele.

```text
Letterboxd
    ↓
RSS
    ↓
scripts/letterboxd/sync.py
    ↓
data/filmes.json
    ↓
layouts/filmes/list.html
    ↓
/filmes/
```

O script busca o feed, interpreta os dados e gera um arquivo que o Hugo consegue consumir diretamente.

A estrutura ficou separada em três responsabilidades.

```text
scripts/letterboxd/sync.py   → coleta e normaliza
data/filmes.json             → armazena os dados
layouts/filmes/list.html     → apresenta os dados
```

Isso é mais importante do que parece.

O template não precisa saber buscar RSS.

O Python não precisa saber montar HTML.

E o conteúdo não fica preso no código.




---

## Classificação automática

Eu também não queria selecionar manualmente se um filme era bom, mediano ou ruim.

A nota já contém essa informação.

Então defini três categorias:

```text
0.5 até 2.0 → Filme Lixo
2.5 até 3.5 → Filme que Existe
4.0 até 5.0 → Filme Top
```

A regra fica no processamento.

Algo conceitualmente simples:

```python
def classificar_filme(nota):
    if nota <= 2.0:
        return "Filme Lixo"

    if nota <= 3.5:
        return "Filme que Existe"

    return "Filme Top"
```

Não existe motivo para armazenar manualmente uma informação que pode ser derivada de outra.

Se a nota é `4.5`, a categoria já está determinada.

Duplicar isso seria criar duas fontes de verdade para a mesma coisa.

---

## O problema do RSS

Depois apareceu um detalhe importante.

RSS não é banco de dados.

O feed do Letterboxd entrega os registros recentes. Se eu simplesmente sobrescrevesse `filmes.json` toda vez que o script rodasse, filmes antigos poderiam desaparecer do SouthGhost conforme saíssem do feed.

Então a sincronização precisou deixar de ser apenas:

```text
baixar → substituir
```

e passar a funcionar como:

```text
dados existentes
      +
dados encontrados no RSS
      ↓
mesclar
      ↓
remover duplicados
      ↓
salvar
```

O JSON local passou a funcionar como histórico.

Isso muda bastante a arquitetura.

O Letterboxd continua sendo a origem das novas avaliações, mas o SouthGhost não depende de o RSS manter eternamente tudo que já apareceu nele.

<!-- PRINT 02 -->
![Script de sincronização do Letterboxd](/imagens/posts/filmes-videos/letterboxd-sync.png)

---

## A página de filmes

Com os dados resolvidos, a parte seguinte foi apresentação.

O Hugo carrega diretamente `data/filmes.json`.

```go-html-template
{{ $filmes := site.Data.filmes }}
```

Depois o template percorre os registros e monta os cards.

A página ganhou filtros e três grupos baseados nas notas:

```text
Filme Top
Filme que Existe
Filme Lixo
```

Também adicionei uma sidebar para navegar pelo histórico e reorganizei o grid para funcionar melhor em telas grandes e pequenas.

A estrutura principal acabou ficando nesse formato:

```go-html-template
{{ range $filmes }}
  <article class="sg-filme-card">
    <a href="{{ .link }}">
      <img
        src="{{ .poster }}"
        alt="{{ .titulo }}"
        loading="lazy"
      >
    </a>

    <div class="sg-filme-conteudo">
      <h3>{{ .titulo }}</h3>
      <span>{{ .ano }}</span>

      <p>{{ .review }}</p>
    </div>
  </article>
{{ end }}
```

Não existe framework JavaScript renderizando a página.

O Hugo lê JSON e cospe HTML.

Para esse caso, é suficiente.

<!-- PRINT 03 -->
![Template da página de filmes](/imagens/posts/filmes-videos/template-filmes.png)

---

## Depois veio o YouTube

Quando a página de filmes estava funcionando, apareceu outro problema muito parecido, tenho playlists no YouTube que funcionam praticamente como favoritos organizados...

História, vídeos reflexivos, alguns canais específicos e coisas que quero guardar

Poderia simplesmente colocar links para essas playlists.

Mas queria que elas fizessem parte do próprio SouthGhost. A arquitetura do Letterboxd já tinha mostrado o caminho.

```text
Playlists do YouTube
        ↓
Feed XML
        ↓
scripts/youtube/sync.py
        ↓
data/videos.json
        ↓
layouts/videos/list.html
        ↓
/videos/
```

De novo: nenhum banco de dados.

E nenhuma API oficial com autenticação, chave ou quota para resolver um problema que não precisava disso.

---

## As playlists viraram configuração

Eu não queria colocar IDs de playlists espalhados pelo código Python.

Criei então um arquivo separado:

```json
{
  "historia": {
    "nome": "História",
    "playlist_id": "ID_DA_PLAYLIST"
  },
  "bode": {
    "nome": "É o Bode",
    "playlist_id": "ID_DA_PLAYLIST"
  },
  "reflexivos": {
    "nome": "Reflexivos",
    "playlist_id": "ID_DA_PLAYLIST"
  },
  "goats": {
    "nome": "GOATs",
    "playlist_id": "ID_DA_PLAYLIST"
  }
}
```

O script não precisa conhecer minhas categorias.

Ele só sabe ler configuração.

Se amanhã eu criar outra playlist, a mudança deveria acontecer nos dados e não exigir que eu espalhe mais uma condição pelo código.

<!-- PRINT 04 -->
![Configuração das playlists](/imagens/posts/filmes-videos/youtube-playlists.png)

---

## Lendo os feeds do YouTube

O YouTube também fornece feed XML para playlists.

O Python monta a URL:

```python
def carregar_feed(playlist_id):
    url = (
        "https://www.youtube.com/feeds/videos.xml"
        f"?playlist_id={playlist_id}"
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=20
    ) as response:
        return response.read()
```

Depois o XML é processado e transformado em uma estrutura muito mais simples para o Hugo:

```json
{
  "categoria": "goats",
  "categoria_nome": "GOATs",
  "titulo": "Título do vídeo",
  "canal": "Nome do canal",
  "video_id": "...",
  "url": "...",
  "thumbnail": "...",
  "publicado_em": "..."
}
```

Esse JSON é a fronteira entre coleta e apresentação.

O Hugo não sabe que originalmente aquilo era XML.

E não precisa saber.

<!-- PRINT 05 -->
![Sincronização dos feeds do YouTube](/imagens/posts/filmes-videos/youtube-sync.png)

---

## Renderizando os vídeos

No template:

```go-html-template
{{ $videos := site.Data.videos }}

{{ range $videos }}

  <article
    class="sg-video-card"
    data-category="{{ .categoria }}"
  >

    <a
      href="{{ .url }}"
      target="_blank"
      rel="noopener noreferrer"
    >

      <img
        src="{{ .thumbnail }}"
        alt="{{ .titulo }}"
        loading="lazy"
      >

      <h2>
        {{ .titulo }}
      </h2>

      <p>
        {{ .canal }}
      </p>

    </a>

  </article>

{{ end }}
```

Também coloquei filtros por categoria.

Nesse caso um pouco de JavaScript resolve:

```javascript
function aplicarFiltro(selected) {
  cards.forEach((card) => {
    const category = card.dataset.category;

    const visible =
      selected === "all" ||
      selected === category;

    card.classList.toggle(
      "is-hidden",
      !visible
    );
  });
}
```

É JavaScript para interação.

Não JavaScript para reconstruir no cliente algo que o Hugo já poderia ter renderizado antes.

Essa distinção parece pequena, mas evita transformar qualquer página com quatro botões em uma SPA.

---

## Automatizando tudo

Ainda existia uma falha no processo.

Eu tinha scripts automáticos, mas precisava executá-los manualmente.

Isso não é automação.

É só um comando que faz bastante coisa.

A etapa seguinte foi colocar a sincronização no GitHub Actions.

Agora o processo pode executar os scripts, atualizar os JSONs e deixar o próprio fluxo de build publicar o resultado.

No caso do Letterboxd:

```text
nova avaliação
      ↓
RSS
      ↓
GitHub Actions
      ↓
sync.py
      ↓
filmes.json
      ↓
Hugo
      ↓
GitHub Pages
```

No YouTube:

```text
playlist alterada
      ↓
Feed XML
      ↓
GitHub Actions
      ↓
sync.py
      ↓
videos.json
      ↓
Hugo
      ↓
GitHub Pages
```

A diferença é que agora meu computador não faz parte da infraestrutura necessária para manter essas páginas atualizadas.

Isso é o ponto importante.

<!-- PRINT 07 -->
![Workflow de sincronização no GitHub Actions](/imagens/posts/filmes-videos/github-actions.png)

---

## Por que não usar uma API?

Porque primeiro vem o problema.

Depois a ferramenta.

Para o que eu precisava, os feeds públicos já entregavam os dados necessários.

Adicionar API significaria começar a lidar com coisas como:

```text
credenciais
tokens
segredos
quotas
bibliotecas
autenticação
renovação
mais pontos de falha
```

Nada disso seria tecnicamente impressionante.

Seria apenas mais infraestrutura.

Se algum dia os feeds deixarem de entregar o que preciso, aí existe motivo para rever a arquitetura.

Antes disso, não.

---

## O SouthGhost continua estático

Essa foi a parte que mais gostei dessas duas implementações.

Mesmo adicionando fontes externas e sincronização automática, o resultado final continua sendo um site estático.

```text
Letterboxd ──┐
             ├── Python → JSON → Hugo → HTML
YouTube ─────┘
```

Não existe servidor Python atendendo usuário.

Não existe banco de dados.

Não existe chamada ao Letterboxd toda vez que alguém abre `/filmes/`.

Não existe chamada ao YouTube toda vez que alguém abre `/videos/`.

A complexidade fica no momento de sincronização e build.

O visitante recebe arquivos prontos.

É uma arquitetura simples, mas não simplista.

E, por enquanto, é exatamente o tipo de coisa que quero manter no SouthGhost.