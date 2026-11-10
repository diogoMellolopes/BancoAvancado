import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")
DATABASE = os.getenv("NEO4J_DATABASE")

class Database:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            URI,
            auth=(USERNAME, PASSWORD)
        )
    def verify_connection(self):
        self.driver.verify_connectivity()

    def close(self):
        self.driver.close()

    def create_constraints(self):
        constraints = [
            """
            CREATE CONSTRAINT anime_mal_id IF NOT EXISTS
            FOR (a:Anime)
            REQUIRE a.mal_id IS UNIQUE
            """,

            """
            CREATE CONSTRAINT genre_name IF NOT EXISTS
            FOR (g:Genre)
            REQUIRE g.name IS UNIQUE
            """,

            """
            CREATE CONSTRAINT theme_name IF NOT EXISTS
            FOR (t:Theme)
            REQUIRE t.name IS UNIQUE
            """,

            """
            CREATE CONSTRAINT demographic_name IF NOT EXISTS
            FOR (d:Demographic)
            REQUIRE d.name IS UNIQUE
            """,

            """
            CREATE CONSTRAINT studio_name IF NOT EXISTS
            FOR (s:Studio)
            REQUIRE s.name IS UNIQUE
            """,

            """
            CREATE CONSTRAINT producer_name IF NOT EXISTS
            FOR (p:Producer)
            REQUIRE p.name IS UNIQUE
            """
        ]
        with self.driver.session(database=DATABASE) as session:
            for query in constraints:
                session.run(query)

    def clear_database(self):
        query = """
        MATCH (n)
        DETACH DELETE n
        """

        with self.driver.session(database=DATABASE) as session:
            session.run(query)

    @staticmethod
    def extract_names(items):
        names = []
        if not isinstance(items, list):
            return names

        for item in items:
            if isinstance(item, dict):
                name = item.get("name")
            elif isinstance(item, str):
                name = item
            else:
                name = None

            if name and name not in names:
                names.append(name)
        return names

    @classmethod
    def prepare_anime(cls, anime):
        return {
            "mal_id": anime.get("mal_id"),

            "title": anime.get("title"),
            "title_english": anime.get("title_english"),

            "score": anime.get("score"),
            "episodes": anime.get("episodes"),

            "type": anime.get("type"),
            "url": anime.get("url"),

            "genres": cls.extract_names(
                anime.get("genres", [])
            ),

            "themes": cls.extract_names(
                anime.get("themes", [])
            ),

            "demographics": cls.extract_names(
                anime.get("demographics", [])
            ),

            "studios": cls.extract_names(
                anime.get("studios", [])
            ),

            "producers": cls.extract_names(
                anime.get("producers", [])
            )
        }

    def save_anime_batch(self, anime_list):
        batch = [
            self.prepare_anime(anime)
            for anime in anime_list
            if anime.get("mal_id") is not None
        ]
        unique_anime = {
            anime["mal_id"]: anime
            for anime in batch
        }
        batch = list(unique_anime.values())

        query = """
        UNWIND $batch AS item
        MERGE (a:Anime {mal_id: item.mal_id})
        SET
            a.title = item.title,
            a.title_english = item.title_english,
            a.score = item.score,
            a.episodes = item.episodes,
            a.type = item.type,
            a.url = item.url
        FOREACH (name IN item.genres |
            MERGE (g:Genre {name: name})
            MERGE (a)-[:HAS_GENRE]->(g)
        )
        FOREACH (name IN item.themes |
            MERGE (t:Theme {name: name})
            MERGE (a)-[:HAS_THEME]->(t)
        )
        FOREACH (name IN item.demographics |
            MERGE (d:Demographic {name: name})
            MERGE (a)-[:TARGETS]->(d)
        )
        FOREACH (name IN item.studios |
            MERGE (s:Studio {name: name})
            MERGE (a)-[:ANIMATED_BY]->(s)
        )
        FOREACH (name IN item.producers |
            MERGE (p:Producer {name: name})
            MERGE (a)-[:PRODUCED_BY]->(p)
        )
        """

        tamanho_lote = 500
        total = len(batch)

        with self.driver.session(database=DATABASE) as session:
            for inicio in range(0, total, tamanho_lote):
                lote = batch[inicio:inicio + tamanho_lote]

                session.execute_write(
                    lambda tx: tx.run(
                        query,
                        batch=lote
                    ).consume()
                )