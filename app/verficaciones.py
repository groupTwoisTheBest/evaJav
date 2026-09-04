from fastapi import Form, APIRouter, HTTPException
from fastapi.responses import RedirectResponse

data = [
    {"nombre": "1234", "contrasenna": "m", "redirect": "/seleccionatuprofesor"},
    {"nombre": "1025657456", "contrasenna": "MJAVIERA", "redirect": "/seleccionatuprofesor"},
    {"nombre": "1020113554", "contrasenna": "MJAVIERA", "redirect": "/seleccionatuprofesor"},
    {"nombre": "fabioman", "contrasenna": "MJAVIERA", "redirect": "/configuracion"}
]

router = APIRouter()

async def verificar_usuario(nombre: str = Form(...), contrasenna: str = Form(...)):
    for user in data:
        if user["nombre"] == nombre and user["contrasenna"] == contrasenna:
            return RedirectResponse("/seleccionatuprofesor", status_code=303)
        else:
            return RedirectResponse("/", status_code=303)
            
            
    
