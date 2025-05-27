from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class PersonType(str, Enum):
    actor = "actor"
    director = "director"
    writer = "writer"


class AbstractModel(BaseModel):
    id: UUID


class PersonInFilm(AbstractModel):
    name: str


class GenresES(AbstractModel):
    name: str


class PersonsES(PersonInFilm):
    role: Optional[List[PersonType]] = None
    film_ids: Optional[List[UUID]] = None


class MoviesES(AbstractModel):
    title: str
    imdb_rating: Optional[float] = None
    description: Optional[str] = None
    genres: Optional[List[str]] = None
    directors: Optional[List[PersonInFilm]] = None
    actors: Optional[List[PersonInFilm]] = None
    writers: Optional[List[PersonInFilm]] = None
    directors_names: Optional[List[str]] = None
    actors_names: Optional[List[str]] = None
    writers_names: Optional[List[str]] = None
