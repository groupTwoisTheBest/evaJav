from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

LinkJS = [
    {"src": "/static/js/index.js"},
    {"src": "/static/js/sele_prof.js"},
    {"src": "/static/js/cal_plataform.js"},
]
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"linkJs": LinkJS[0]})

@app.get("/seleccionatuprofesor", response_class=HTMLResponse)
async def read_seleccionatuprofesor(request: Request,):
    return templates.TemplateResponse(request=request, name="selectProfesor.html", context={"linkJs": LinkJS[1]})

@app.get("/calificaElProfesor", response_class=HTMLResponse)
async def read_calificaElProfesor(request: Request):
    return templates.TemplateResponse(request=request, name="calification_plataform.html", context={"linkJs": LinkJS[2]})
@app.get("/Agradecimiento", response_class=HTMLResponse)
async def read_agradecimiento(request: Request):
    return templates.TemplateResponse(request=request, name="certificado.html", context={"linkJs": LinkJS[0]})