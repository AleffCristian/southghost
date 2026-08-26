# Como criar um artigo

## Opção 1 — pelo Hugo

```powershell
hugo new content blog/meu-artigo.md
```

Abra o arquivo criado e ajuste:

```yaml
---
title: "Título"
date: 2026-08-26
draft: false
description: "Resumo curto."
featured: false
tags:
  - tecnologia
---
```

## Opção 2 — manualmente

Crie:

```text
content/blog/nome-do-artigo.md
```

Use o mesmo front matter acima.

## Destaques

Para aparecer na caixa Destaques:

```yaml
featured: true
```

Nada precisa ser alterado no HTML.
