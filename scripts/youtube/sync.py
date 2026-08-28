import json
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]

PLAYLISTS_FILE = ROOT_DIR / "scripts" / "youtube" / "playlists.json"
OUTPUT_FILE = ROOT_DIR / "data" / "videos.json"


NAMESPACES = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
}


def carregar_playlists():
    with PLAYLISTS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


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

    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read()


def ler_texto(elemento):
    if elemento is None:
        return ""

    return elemento.text or ""


def processar_playlist(slug, playlist):
    playlist_id = playlist.get("playlist_id", "").strip()
    nome = playlist.get("nome", slug)

    if not playlist_id:
        print(f"[IGNORADO] {nome}: playlist sem ID")
        return []

    try:
        xml = carregar_feed(playlist_id)
        root = ET.fromstring(xml)

    except Exception as error:
        print(f"[ERRO] {nome}: {error}")
        return []

    videos = []

    for entry in root.findall("atom:entry", NAMESPACES):
        video_id = ler_texto(
            entry.find("yt:videoId", NAMESPACES)
        )

        if not video_id:
            continue

        titulo = ler_texto(
            entry.find("atom:title", NAMESPACES)
        )

        canal = ler_texto(
            entry.find("atom:author/atom:name", NAMESPACES)
        )

        publicado_em = ler_texto(
            entry.find("atom:published", NAMESPACES)
        )

        videos.append(
            {
                "categoria": slug,
                "categoria_nome": nome,
                "titulo": titulo,
                "canal": canal,
                "video_id": video_id,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "thumbnail": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                "publicado_em": publicado_em,
            }
        )

    print(f"[OK] {nome}: {len(videos)} vídeo(s)")

    return videos


def salvar_videos(videos):
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            videos,
            file,
            ensure_ascii=False,
            indent=2,
        )


def main():
    playlists = carregar_playlists()

    videos = []

    for slug, playlist in playlists.items():
        videos.extend(
            processar_playlist(
                slug,
                playlist,
            )
        )

    salvar_videos(videos)

    print()
    print(f"{len(videos)} vídeo(s) salvos em:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()