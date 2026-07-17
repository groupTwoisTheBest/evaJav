from fastapi import FastAPI, Request, Form, status
from fastapi.responses import RedirectResponse, PlainTextResponse, HTMLResponse
from fastapi.templating import Jinja2Templates


app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Ruta que procesa el formulario mediante método POST
@app.post("../app/index.py")
async def login(username: str = Form(...), password: str = Form(...)):

    # 1. Tu validación original (FastAPI ya capturó los datos en las variables)
    if username == "1234" and password == "M":

        # 2. Redireccionar a la segunda parte
        # El estado 303 es clave para redireccionar de un POST a un GET de forma segura
        return RedirectResponse(url="/seleccionatuprofesor", status_code=status.HTTP_303_SEE_OTHER)
    else:
        return PlainTextResponse("Usuario o contraseña incorrectos", status_code=401)

@app.get("/seleccionatuprofesor", response_class=HTMLResponse)
async def read_seleccionatuprofesor(request: Request,):
    return templates.TemplateResponse(request=request, name="selectProfesor.html", context={})