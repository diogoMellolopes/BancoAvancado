from api import get_top_anime
from database import Database

def main():
    db = Database()

    try:

        db.verify_connection()

        anime_list = get_top_anime(total=10000)
        if len(anime_list) < 10000:
            raise Exception(
                "Não foram encontrados os animes necessários"
            )

        db.clear_database()
        db.create_constraints()
        db.save_anime_batch(anime_list)
    except Exception as error:
        print(error)
    finally:
        db.close()

if __name__ == "__main__":
    main()