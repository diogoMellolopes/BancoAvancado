from database import DATABASE
from api import get_related_anime_ids

WEIGHTS = {
    "genres": 2,
    "themes": 4,
    "demographics": 3,
    "studios": 2,
    "producers": 1
}

QUERY_RECOMMENDATIONS = """
MATCH (source:Anime {mal_id: $mal_id})

MATCH (source)-[]->(feature)<-[]-(candidate:Anime)

WHERE candidate <> source
AND NOT (candidate.mal_id IN $excluded_ids)

WITH DISTINCT source, candidate

WITH
    candidate,

    [(source)-[:HAS_GENRE]->(g:Genre)<-[:HAS_GENRE]-(candidate)
        | g.name] AS sharedGenres,

    [(source)-[:HAS_THEME]->(t:Theme)<-[:HAS_THEME]-(candidate)
        | t.name] AS sharedThemes,

    [(source)-[:TARGETS]->(d:Demographic)<-[:TARGETS]-(candidate)
        | d.name] AS sharedDemographics,

    [(source)-[:ANIMATED_BY]->(s:Studio)<-[:ANIMATED_BY]-(candidate)
        | s.name] AS sharedStudios,

    [(source)-[:PRODUCED_BY]->(p:Producer)<-[:PRODUCED_BY]-(candidate)
        | p.name] AS sharedProducers

WITH
    candidate,
    sharedGenres,
    sharedThemes,
    sharedDemographics,
    sharedStudios,
    sharedProducers,

    size(sharedGenres) * $weight_genres +
    size(sharedThemes) * $weight_themes +
    size(sharedDemographics) * $weight_demographics +
    size(sharedStudios) * $weight_studios +
    size(sharedProducers) * $weight_producers
    AS similarity

RETURN
    candidate.mal_id AS mal_id,
    candidate.title AS title,
    candidate.score AS score,

    similarity AS similarity,

    sharedGenres AS shared_genres,
    sharedThemes AS shared_themes,
    sharedDemographics AS shared_demographics,
    sharedStudios AS shared_studios,
    sharedProducers AS shared_producers

ORDER BY similarity DESC, score DESC
LIMIT $limit
"""

def recommend_anime(
    db,
    mal_id,
    include_related=True,
    limit=10
):
    excluded_ids = [mal_id]

    with db.driver.session(database=DATABASE) as session:
        source_exists = session.run(
            """
            MATCH (a:Anime {mal_id: $mal_id})
            RETURN count(a) > 0 AS exists
            """,
            mal_id=mal_id
        ).single()["exists"]

        if not include_related:
            related_ids = get_related_anime_ids(mal_id)
            excluded_ids.extend(related_ids)
            excluded_ids = list(set(excluded_ids))

        parameters = {
            "mal_id": mal_id,
            "excluded_ids": excluded_ids,
            "limit": limit,

            "weight_genres": WEIGHTS["genres"],
            "weight_themes": WEIGHTS["themes"],
            "weight_demographics": WEIGHTS["demographics"],
            "weight_studios": WEIGHTS["studios"],
            "weight_producers": WEIGHTS["producers"]
        }

        result = session.run(
            QUERY_RECOMMENDATIONS,
            parameters
        )
        recommendations = result.data()

    return recommendations