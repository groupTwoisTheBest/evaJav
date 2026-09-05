from app.dependencias import APIRouter, Depends, Request, Form, status, RedirectResponse, PlainTextResponse, HTMLResponse, Jinja2Templates, logger
from app.repositorio import inicio_sesion as autenticar_estudiante, registrar_estudiante, existe_email
from app.dependencias import ConnectionDep
from app.esquemas import crear_estudiante

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def inicio(request: Request):
    return templates.TemplateResponse(request=request, name="inicio.html", context={})


@router.get("/inicio-sesion", response_class=HTMLResponse)
async def inicio_sesion(request: Request, error: str = None):
    return templates.TemplateResponse(request=request, name="index.html", context={"error": error})


@router.get("/registrarse", response_class=HTMLResponse)
async def registrarse(request: Request):
    return templates.TemplateResponse(request=request, name="registrarse.html", context={})


@router.post("/registrarse")
async def registrarse_post(nombre: str = Form(...), contrasenna: str = Form(...)):
    # TODO: Implementar lógica de persistencia de registro (inserción en DB, hashing de contraseña, etc.)
    return PlainTextResponse("TODO: Implementar lógica de registro", status_code=501)


@router.post("/login")
async def login(
    conn: ConnectionDep,
    email: str = Form(...),
    contrasenna: str = Form(...),
):
    try:
        user = await autenticar_estudiante(conn, email, contrasenna)
    except Exception as e:
        logger.error(f"Error de conexión a la base de datos durante login: {e}")
        return RedirectResponse(url="/inicio-sesion?error=1", status_code=status.HTTP_303_SEE_OTHER)
    if user is None:
        return RedirectResponse(url="/inicio-sesion?error=1", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/seleccionatuprofesor", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/nuevo-usuario")
async def nuevo_usuario(
    request: Request,
    conn: ConnectionDep,
    nombre: str = Form(...),
    email: str = Form(...),
    contrasenna: str = Form(...),
    grado: int = Form(...)
):
    if await existe_email(conn, email):
        return templates.TemplateResponse(request=request, name="registrarse.html", context={"error": "El correo ya está registrado."})
    estudiante = crear_estudiante(nombre=nombre, email=email, contrasenna=contrasenna)
    await registrar_estudiante(conn, estudiante.nombre, estudiante.email, estudiante.contrasenna, grado)
    return templates.TemplateResponse(request=request, name="registrarse.html", context={"message": "Registrado exitosamente."})


@router.get("/seleccionatuprofesor", response_class=HTMLResponse)
async def read_seleccionatuprofesor(request: Request):
    return templates.TemplateResponse(request=request, name="selectProfesor.html", context={})


@router.post("/seleccionatuprofesor")
async def seleccionar_profesor(request: Request, maestro: str = Form(...)):
    if not maestro:
        return templates.TemplateResponse(
            request=request,
            name="selectProfesor.html",
            context={"error": "Selecciona un profesor"}
        )
    return templates.TemplateResponse(
        request=request,
        name="calification_plataform.html",
        context={"maestro": maestro}
    )


@router.get("/administrador", response_class=HTMLResponse)
async def read_administrador(request: Request):
    return templates.TemplateResponse(request=request, name="administradorMain.html", context={})


@router.get("/gestionProfesores", response_class=HTMLResponse)
async def read_gestion_profesores(request: Request):
    return templates.TemplateResponse(request=request, name="gestionProfesores.html", context={})


@router.get("/gestionProfesoresInformacion", response_class=HTMLResponse)
async def read_gestion_profesores_informacion(request: Request):
    return templates.TemplateResponse(request=request, name="gestionProfesoresInformacion.html", context={})


@router.get("/centroEstadistico", response_class=HTMLResponse)
async def read_centro_estadistico(request: Request):
    return templates.TemplateResponse(request=request, name="centroEstadistico.html", context={})


@router.get("/configuracion", response_class=HTMLResponse)
async def configuracion(request: Request):
    return templates.TemplateResponse(request=request, name="configuracion.html", context={})


@router.get("/calificaElProfesor", response_class=HTMLResponse)
async def read_calificaElProfesor(request: Request):
    return templates.TemplateResponse(request=request, name="calification_plataform.html", context={"maestro": ""})


@router.post("/calificaElProfesor")
async def enviar_calificacion(
    request: Request,
    maestro: str = Form(...),
    explicationsTopics: str = Form(...),
    actitudinal: str = Form(...),
    classActivity: str = Form(...)
):
    if not explicationsTopics or not actitudinal or not classActivity:
        return templates.TemplateResponse(
            request=request,
            name="calification_plataform.html",
            context={"maestro": maestro, "error": "Selecciona una nota para cada casilla"}
        )
    return RedirectResponse(url="/Agradecimiento", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/Agradecimiento", response_class=HTMLResponse)
async def read_agradecimiento(request: Request):
    return templates.TemplateResponse(request=request, name="certificado.html", context={})
