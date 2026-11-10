import time
import requests

BASE_URL = "https://api.tenrai.org/v1"

MAX_ATTEMPTS = 5
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.35

def make_request(session, url, params=None):
    for tentativa in range(MAX_ATTEMPTS):

        try:
            response = session.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT
            )
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", 5)

                try:
                    espera = float(retry_after)
                except (ValueError, TypeError):
                    espera = 5

                time.sleep(espera)
                continue

            if response.status_code >= 500:
                espera = 2 ** tentativa

                print(
                    f"{response.status_code}"
                )

                time.sleep(espera)
                continue

            response.raise_for_status()
            return response

        except requests.RequestException as error:

            if tentativa == MAX_ATTEMPTS - 1:
                raise RuntimeError(
                    f"{error}"
                ) from error

            espera = 2 ** tentativa
            time.sleep(espera)

def get_top_anime(total=10000):
    anime_list = []
    anime_ids = set()

    limit = 100
    total_pages = (total + limit - 1) // limit

    with requests.Session() as session:
        for page in range(1, total_pages + 1):
            url = f"{BASE_URL}/top/anime"

            params = {
                "page": page,
                "limit": limit,
                "sfw": "true"
            }

            response = make_request(
                session,
                url,
                params
            )
            dados = response.json()
            pagina_animes = dados.get("data", [])

            if not pagina_animes:
                break

            novos = 0

            for anime in pagina_animes:

                if not isinstance(anime, dict):
                    continue

                mal_id = anime.get("mal_id")

                if mal_id is None:
                    continue

                if mal_id in anime_ids:
                    continue

                anime_ids.add(mal_id)
                anime_list.append(anime)
                novos += 1

            if len(anime_list) >= total:
                break

            if novos == 0:
                break

            time.sleep(REQUEST_DELAY)

    return anime_list[:total]

def get_related_anime_ids(mal_id):
    url = f"{BASE_URL}/anime/{mal_id}/relations"

    with requests.Session() as session:
        response = make_request(
            session,
            url,
            params={"sfw": "true"}
        )

        dados = response.json()
    relations = dados.get("data", [])

    related_ids = set()
    for relation in relations:
        if not isinstance(relation, dict):
            continue

        entries = relation.get("entry", [])
        if not isinstance(entries, list):
            continue

        for entry in entries:
            if not isinstance(entry, dict):
                continue

            if entry.get("type") != "anime":
                continue
            related_id = entry.get("mal_id")

            if isinstance(related_id, int):
                related_ids.add(related_id)

    return sorted(related_ids)