from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})

@app.get("/seleccionatuprofesor", response_class=HTMLResponse)
async def read_seleccionatuprofesor(request: Request,):
    return templates.TemplateResponse(request=request, name="selectProfesor.html", context={})
    
@app.get("/configuracion", response_class=HTMLResponse)
async def configuracion(request: Request,):
    return templates.TemplateResponse(request=request, name="configuracion.html", context={})

@app.get("/calificaElProfesor", response_class=HTMLResponse)
async def read_calificaElProfesor(request: Request):
    return templates.TemplateResponse(request=request, name="calification_plataform.html", context={})

@app.get("/Agradecimiento", response_class=HTMLResponse)
async def read_agradecimiento(request: Request):
    return templates.TemplateResponse(request=request, name="certificado.html", context={})