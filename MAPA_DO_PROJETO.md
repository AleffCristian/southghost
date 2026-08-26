# Mapa do projeto

Este arquivo existe para você fuçar sem precisar adivinhar onde cada coisa mora.

## `hugo.toml`

É a configuração central.

Aqui ficam:

- nome do site;
- idioma;
- Hextra;
- menu;
- busca;
- tema claro/escuro;
- configurações do blog.

Se algo afeta o site inteiro, procure aqui primeiro.

## `content/`

É onde mora o conteúdo.

### `content/blog/`

Cada `.md` é um artigo.

Exemplo de front matter:

```yaml
---
title: "Meu artigo"
date: 2026-08-26
description: "Resumo curto."
featured: false
tags:
  - hugo
  - git
---
```

`featured: true` coloca o artigo em **Destaques**.

### `content/docs/`

Documentação técnica.

### `content/sobre/`

Página Sobre.

## `layouts/home.html`

É a Home customizada.

Ela:

1. busca os posts do blog;
2. ordena por data;
3. separa Destaques;
4. agrupa por mês;
5. gera a sidebar automaticamente.

Se você quiser mudar a **estrutura** da Home, é aqui.

## `assets/css/custom.css`

Visual.

Mude valores pequenos e atualize o navegador:

```css
--sg-accent: #b84a2d;
```

Troque essa cor e veja o que acontece.

## `assets/js/home.js`

Comportamento da Home:

- Mostrar/Ocultar Destaques;
- Lista/Grade;
- memorizar Lista/Grade;
- destacar o mês atual na sidebar.

Quebrou comportamento de botão? Procure aqui.

## Experimentos seguros

Algumas coisas boas para testar:

1. troque `--sg-accent`;
2. mude `max-width`/largura em `.sg-shell`;
3. altere `featured: false` para `true`;
4. crie um artigo com data de outro mês;
5. altere `repeat(2, ...)` para `repeat(3, ...)` na Grade;
6. mude os nomes do menu em `hugo.toml`.

Use Git antes de experiências maiores:

```powershell
git status
git add .
git commit -m "chore: save working state"
```

A regra é simples: primeiro checkpoint, depois caos.
