from fastapi import Form, APIRouter, HTTPException
from fastapi.responses import RedirectResponse

data = [
    {"username": "1234", "password": "m", "redirect": "/seleccionatuprofesor"},
    {"username": "1025657456", "password": "MJAVIERA", "redirect": "/seleccionatuprofesor"},
    {"username": "1020113554", "password": "MJAVIERA", "redirect": "/seleccionatuprofesor"},
    {"username": "fabioman", "password": "MJAVIERA", "redirect": "/configuracion"}
]

router = APIRouter()

async def verificar_usuario(username: str = Form(...), password: str = Form(...)):
    for user in data:
        if user["username"] == username and user["password"] == password:
            return RedirectResponse("/seleccionatuprofesor", status_code=303)
        else:
            return RedirectResponse("/", status_code=303)
            
            
    
