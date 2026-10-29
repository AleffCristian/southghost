# Baixa as imagens de um post a partir do Wikimedia Commons (domínio público).
# A lista fica em scripts\imagens\<slug>.txt, uma imagem por linha:
#   destino.jpg | Arquivo_no_Commons.jpg[;Alternativa.jpg] | largura
# Uso (na raiz do repositório):
#   powershell -ExecutionPolicy Bypass -File scripts\baixar-imagens.ps1 evangelho-da-prosperidade
#   powershell -ExecutionPolicy Bypass -File scripts\baixar-imagens.ps1 -Todos

param(
  [Parameter(Position = 0)][string]$Post,
  [switch]$Todos
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ua = 'SouthGhostBlog/1.0 (https://southghost.com)'   # o Wikimedia exige User-Agent identificável
$pastaListas = Join-Path $PSScriptRoot 'imagens'

if ($Todos) { $listas = Get-ChildItem $pastaListas -Filter *.txt }
elseif ($Post) { $listas = @(Get-Item (Join-Path $pastaListas "$Post.txt")) }
else { Write-Host 'Informe o slug do post ou -Todos.' -ForegroundColor Yellow; exit 1 }

$falhas = 0
foreach ($lista in $listas) {
  $slug = $lista.BaseName
  $destino = Join-Path $PSScriptRoot "..\static\imagens\posts\$slug"
  New-Item -ItemType Directory -Force -Path $destino | Out-Null
  Write-Host "`n== $slug" -ForegroundColor Cyan

  foreach ($linha in Get-Content $lista.FullName -Encoding UTF8) {
    if ($linha -match '^\s*(#|$)') { continue }
    $partes = $linha.Split('|') | ForEach-Object { $_.Trim() }
    $nome, $arquivoCommons = $partes[0], $partes[1]
    $largura = if ($partes.Count -ge 3 -and $partes[2]) { $partes[2] } else { '1280' }
    $alvo = Join-Path $destino $nome
    if (Test-Path $alvo) { Write-Host "ja existe  $nome"; continue }

    # varias alternativas podem vir separadas por ";" - usa a primeira que existir
    $ok = $false
    $erro = ''
    foreach ($alternativa in ($arquivoCommons.Split(';') | ForEach-Object { $_.Trim() } | Where-Object { $_ })) {
      $url = 'https://commons.wikimedia.org/wiki/Special:FilePath/' + [uri]::EscapeDataString($alternativa) + "?width=$largura"
      try {
        Invoke-WebRequest -Uri $url -OutFile $alvo -UserAgent $ua -UseBasicParsing
        Write-Host ("baixado    {0}  ({1} KB)  <- {2}" -f $nome, [math]::Round((Get-Item $alvo).Length / 1KB), $alternativa) -ForegroundColor Green
        $ok = $true
        break
      } catch {
        if (Test-Path $alvo) { Remove-Item $alvo }
        $erro = $_.Exception.Message
      }
      Start-Sleep -Milliseconds 800
    }
    if (-not $ok) { Write-Host "FALHOU     ${nome}: $erro" -ForegroundColor Red; $falhas++ }
    Start-Sleep -Milliseconds 800
  }
}

if ($falhas) { Write-Host "`n$falhas imagem(ns) falharam. Rode de novo; as que ja baixaram sao puladas." -ForegroundColor Yellow }
else { Write-Host "`nPronto." -ForegroundColor Cyan }
