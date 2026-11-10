from database import Database
from recommendations import recommend_anime

def main():
    db = None

    try:
        db = Database()
        db.verify_connection()

        anime_id = 2167
        include_related = False

        recommendations = recommend_anime(
            db=db,
            mal_id=anime_id,
            include_related=include_related,
            limit=10
        )

        for index, anime in enumerate(
            recommendations,
            start=1
        ):
            print(f"{index}. {anime['title']}")
            print(f"   MAL ID: {anime['mal_id']}")
            print(f"   Nota: {anime['score']}")
            print(
                f"   Pontuação de similaridade: "
                f"{anime['similarity']}"
            )

            print(
                f"   Gêneros compartilhados: "
                f"{anime['shared_genres']}"
            )

            print(
                f"   Temas compartilhados: "
                f"{anime['shared_themes']}"
            )

            print(
                f"   Demografias compartilhadas: "
                f"{anime['shared_demographics']}"
            )

            print(
                f"   Estúdios compartilhados: "
                f"{anime['shared_studios']}"
            )

            print(
                f"   Produtoras compartilhadas: "
                f"{anime['shared_producers']}"
            )

            print()

    finally:
        if db is not None:
            db.close()

if __name__ == "__main__":
    main()