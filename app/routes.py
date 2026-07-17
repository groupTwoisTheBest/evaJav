"""routes.py"""

from fastapi import Request, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app import verificac


router = APIRouter()
templates = Jinja2Templates(directory="templates")


def render(request: Request, template: str, **ctx) -> HTMLResponse:

    return templates.TemplateResponse(
        request=request, name=template, context={**ctx}
    )

@router.get("/")
async def read_root(request: Request) -> HTMLResponse:
    return render(request,"index.html")

@router.get("/seleccionatuprofesor")
async def read_seleccionatuprofesor(request: Request,) -> HTMLResponse:
    return render(request,"selectProfesor.html")
    
@router.get("/configuracion")
async def configuracion(request: Request,)->HTMLResponse:
    return render(request,"configuracion.html")

@router.get("/calificaElProfesor")
async def read_calificaElProfesor(request: Request) -> HTMLResponse:
    return render(request,"calification_plataform.html")

@router.get("/Agradecimiento", response_class=HTMLResponse)
async def read_agradecimiento(request: Request)-> HTMLResponse:
    return render(request,"certificado.html")