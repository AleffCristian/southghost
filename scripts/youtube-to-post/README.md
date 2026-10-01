# Gerador de posts a partir de vídeos do YouTube

Esta funcionalidade transforma vídeos selecionados manualmente em rascunhos para o SouthGhost.

Fluxo previsto:

1. Ler `data/youtube-posts.json`.
2. Selecionar somente entradas com `gerar: true`.
3. Validar a URL e os metadados.
4. Obter uma transcrição disponível para o vídeo.
5. Gerar o artigo em Markdown seguindo o padrão do SouthGhost.
6. Gerar ou adicionar imagens de forma controlada.
7. Criar o conteúdo em uma branch própria.
8. Abrir um Pull Request para revisão.
9. Publicar somente depois do merge.

A primeira versão não publica diretamente no `main`.

## Formato de entrada

```json
{
  "url": "https://www.youtube.com/watch?v=XXXXXXXXXXX",
  "slug": "nome-do-artigo",
  "categoria": "reflexivos",
  "gerar": true
}
```

## Segurança

- Nenhuma chave de API deve ficar neste arquivo.
- Segredos devem ser armazenados no GitHub Actions Secrets.
- O workflow será iniciado manualmente na primeira versão.
- Falhas na transcrição ou geração devem interromper o processo.
- O conteúdo gerado será revisado antes da publicação.


## Teste local do gerador

Depois de obter a transcrição:

```powershell
python scripts/youtube-to-post/generate.py
```

O script cria um arquivo em `content/blog/<slug>.md` com `draft: true`.

O gerador inicial não usa IA. Ele apenas transforma a transcrição em um rascunho Markdown, preservando o texto original e preparando a estrutura do Hugo.

O arquivo existente nunca é sobrescrito automaticamente.
