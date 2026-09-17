from typing import Annotated
from pydantic import BaseModel, Field, EmailStr


class CrearEstudiante(BaseModel):
    nombre: Annotated[str, Field(min_length=1, max_length=100)]
    email: EmailStr
    contrasenna: Annotated[str, Field(min_length=8, max_length=100)]
    grado: int


class LoginSchema(BaseModel):
    email: EmailStr
    contrasenna: Annotated[str, Field(min_length=1)]


class RegistroSchema(BaseModel):
    nombre: Annotated[str, Field(min_length=1, max_length=100)]
    contrasenna: Annotated[str, Field(min_length=8, max_length=100)]


class CalificacionSchema(BaseModel):
    maestro: Annotated[str, Field(min_length=1)]
    explicationsTopics: Annotated[str, Field(min_length=1)]
    actitudinal: Annotated[str, Field(min_length=1)]
    classActivity: Annotated[str, Field(min_length=1)]


class SeleccionProfesorSchema(BaseModel):
    maestro: Annotated[str, Field(min_length=1)]
