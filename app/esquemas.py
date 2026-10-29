from pickle import INT
from typing import Annotated
from pydantic import BaseModel, Field, EmailStr


class CrearEstudiante(BaseModel):
    nombre: Annotated[str, Field(min_length=1, max_length=100)]
    email: EmailStr
    contrasenna: Annotated[str, Field(min_length=8, max_length=100)]
    grado: int

class CrearMaestro(BaseModel):
    nombre: Annotated[str, Field(min_length=1, max_length=100)]
    Grado: int
    contrasenna: Annotated[str, Field(min_length=8, max_length=100)]
    especialidad: Annotated[str, Field(min_length=1, max_length=100)] 


class GuardarEstudiante(BaseModel):
    nombre: Annotated[str, Field(min_length=1, max_length=100)]
    email: EmailStr
    grado: int

class GuardarProfesor(BaseModel):
    nombre: Annotated[str, Field(min_length=1, max_length=100)]

class LoginSchema(BaseModel):
    email: EmailStr
    contrasenna: Annotated[str, Field(min_length=1)]




class CalificacionSchema(BaseModel):
    maestro: Annotated[str, Field(min_length=1)]
    explication: Annotated[int, Field()]
    actitudinal: Annotated[int, Field()]
    class_activity: Annotated[int, Field()]
    id_materia: Annotated[int, Field()]


class SeleccionProfesorSchema(BaseModel):
    
    maestro: Annotated[str, Field(min_length=1)]
    id_materia: Annotated[int, Field()]
