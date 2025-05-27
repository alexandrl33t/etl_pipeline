from typing import Optional


def get_movies_query(load_from: Optional[str]) -> str:
    """
    Формирует sql запрос с подставленной временной меткой для индекса movies
    """

    return f"""
SELECT 
    film.id,
    film.rating AS imdb_rating,
    film.title,
    film.description,
    
    ARRAY_AGG(DISTINCT (genre.name)) AS genres,

    ARRAY_AGG(DISTINCT jsonb_build_object('id', person.id, 'name', person.full_name)) 
        FILTER (WHERE person_film.role = 'director') AS directors,
    ARRAY_AGG(DISTINCT person.full_name) 
        FILTER (WHERE person_film.role = 'director') AS directors_names,

    ARRAY_AGG(DISTINCT jsonb_build_object('id', person.id, 'name', person.full_name)) 
        FILTER (WHERE person_film.role = 'actor') AS actors,
    ARRAY_AGG(DISTINCT person.full_name) 
        FILTER (WHERE person_film.role = 'actor') AS actors_names,

    ARRAY_AGG(DISTINCT jsonb_build_object('id', person.id, 'name', person.full_name)) 
        FILTER (WHERE person_film.role = 'writer') AS writers,
    ARRAY_AGG(DISTINCT person.full_name) 
        FILTER (WHERE person_film.role = 'writer') AS writers_names,

    GREATEST(film.modified, MAX(person.modified), MAX(genre.modified)) AS modified

FROM content.film_work film
    LEFT JOIN content.genre_film_work AS genre_film ON film.id = genre_film.film_work_id
    LEFT JOIN content.genre AS genre ON genre_film.genre_id = genre.id
    LEFT JOIN content.person_film_work AS person_film ON film.id = person_film.film_work_id
    LEFT JOIN content.person AS person ON person_film.person_id = person.id

WHERE
    GREATEST(film.modified, person.modified, genre.modified) > '{load_from}'

GROUP BY film.id

ORDER BY GREATEST(film.modified, MAX(person.modified), MAX(genre.modified)) ASC;
    """


def get_genres_query(load_from: Optional[str]) -> str:
    """
    Формирует sql запрос с подставленной временной меткой для индекса genres
    """

    return f"""
SELECT genre.id,
    genre.name,
    genre.modified
FROM content.genre genre
WHERE
    genre.modified > '{load_from}'
GROUP BY genre.id
ORDER BY genre.modified ASC
    """


def get_persons_query(load_from: Optional[str]) -> str:
    """
    Формирует sql запрос с подставленной временной меткой для индекса persons
    """

    return f"""
SELECT person.id,
    person.full_name AS name,
    ARRAY_AGG(DISTINCT person_film.role::text) AS role,
    ARRAY_AGG(DISTINCT person_film.film_work_id::text) AS film_ids,
    person.modified
FROM content.person person
    LEFT JOIN content.person_film_work AS person_film ON person.id = person_film.person_id
WHERE
    person.modified > '{load_from}'
GROUP BY person.id
ORDER BY person.modified ASC
    """


def get_query_by_index(index: str, load_from: Optional[str]) -> str:
    """Формирует нужный sql запрос в зависимости от индекса"""

    if not load_from:
        raise ValueError("For getting sql query datetime string required")

    elif index == "movies":
        return get_movies_query(load_from)

    elif index == "genres":
        return get_genres_query(load_from)

    elif index == "persons":
        return get_persons_query(load_from)

    # можно добавить таким образом остальные индексы

    raise ValueError(f"No query for index {index}")
