from pydantic import BaseModel, Field

class crear_estudiante(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=5, max_length=100)
    contrasenna: str = Field(..., min_length=1, max_length=10)
