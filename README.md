# SouthGhost

Site editorial construído com Hugo + Hextra.

## Requisitos

- Hugo Extended
- Go
- Git

## Rodar localmente

```powershell
hugo mod get
hugo server
```

Abra `http://localhost:1313/`.

## Estrutura principal

- `content/`: textos e páginas
- `layouts/`: templates que sobrescrevem o Hextra
- `assets/css/custom.css`: identidade visual do SouthGhost
- `assets/js/home.js`: Destaques, Lista/Grade e sidebar
- `hugo.toml`: configuração global
