# Baixa as pinturas (domínio público, Wikimedia Commons) do post
# "Política não se mistura com filosofia" para static/imagens/posts/.
# Uso (na raiz do repositório):
#   powershell -ExecutionPolicy Bypass -File scripts\baixar-imagens-politica.ps1

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$destino = Join-Path $PSScriptRoot '..\static\imagens\posts\politica-nao-se-mistura-com-filosofia'
New-Item -ItemType Directory -Force -Path $destino | Out-Null

# Wikimedia exige um User-Agent identificável
$ua = 'SouthGhostBlog/1.0 (https://southghost.com)'
$largura = 1280

$imagens = [ordered]@{
  'goya-sono-da-razao.jpg'           = 'Francisco_José_de_Goya_y_Lucientes_-_The_sleep_of_reason_produces_monsters_(No._43),_from_Los_Caprichos_-_Google_Art_Project.jpg'
  'waterhouse-diogenes.jpg'          = 'John_Waterhouse_-_Diogenes_-_Google_Art_Project.jpg'
  'bruegel-cegos.jpg'                = 'Pieter_Bruegel_the_Elder_(1568)_The_Blind_Leading_the_Blind.jpg'
  'david-morte-de-socrates.jpg'      = 'David_-_The_Death_of_Socrates.jpg'
  'rafael-escola-de-atenas.jpg'      = 'Sanzio_01.jpg'
  'hobbes-leviata.jpg'               = 'Leviathan_by_Thomas_Hobbes.jpg'
  'sylvestre-saque-de-roma.jpg'      = 'Sack_of_Rome_by_the_Visigoths_on_24_August_410_by_JN_Sylvestre_1890.jpg'
  'bosch-prestidigitador.jpg'        = 'Conjurer_Bosch.jpg'
  'goya-duelo-a-garrotazos.jpg'      = 'Francisco_de_Goya_y_Lucientes_-_Duelo_a_garrotazos.jpg'
  'gerome-diogenes.jpg'              = 'Jean-Léon_Gérôme_-_Diogenes_-_Walters_37131.jpg'
  'friedrich-monge-a-beira-mar.jpg'  = 'Caspar_David_Friedrich_-_Der_Mönch_am_Meer_-_Google_Art_Project.jpg'
}

$falhas = @()
foreach ($item in $imagens.GetEnumerator()) {
  $arquivo = Join-Path $destino $item.Key
  if (Test-Path $arquivo) { Write-Host "ja existe  $($item.Key)"; continue }
  $url = 'https://commons.wikimedia.org/wiki/Special:FilePath/' + [uri]::EscapeDataString($item.Value) + "?width=$largura"
  try {
    Invoke-WebRequest -Uri $url -OutFile $arquivo -UserAgent $ua -UseBasicParsing
    $kb = [math]::Round((Get-Item $arquivo).Length / 1KB)
    Write-Host ("baixado    {0}  ({1} KB)" -f $item.Key, $kb) -ForegroundColor Green
  } catch {
    if (Test-Path $arquivo) { Remove-Item $arquivo }
    Write-Host "FALHOU     $($item.Key): $($_.Exception.Message)" -ForegroundColor Red
    $falhas += $item.Key
  }
  Start-Sleep -Milliseconds 800
}

if ($falhas.Count) { Write-Host "`n$($falhas.Count) imagem(ns) falharam. Rode de novo; as que ja baixaram sao puladas." -ForegroundColor Yellow }
else { Write-Host "`nPronto: $($imagens.Count) imagens em $destino" -ForegroundColor Cyan }
