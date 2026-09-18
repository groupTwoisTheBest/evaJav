from typing import Annotated
from app.dependencias import APIRouter, Depends, Request, Form, status, RedirectResponse, PlainTextResponse, HTMLResponse, Jinja2Templates, logger, ConnectionDep, CurrentUserDep
from app.repositorio import inicio_sesion as autenticar_estudiante, registrar_estudiante, existe_email, inicio_sesion_admin, select_profesor, nombre_estudiante, registrar_calificacion
from app.esquemas import CrearEstudiante, LoginSchema, CalificacionSchema, RegistroSchema, SeleccionProfesorSchema
from app.seguridad import create_token, verify_token

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
async def registrarse_post(datos: Annotated[RegistroSchema, Form()]):
    # TODO: Implementar lógica de persistencia de registro (inserción en DB, hashing de contraseña, etc.)
    return PlainTextResponse("TODO: Implementar lógica de registro", status_code=501)


@router.post("/login")
async def login(
    conn: ConnectionDep,
    datos: Annotated[LoginSchema, Form()]
):
    try:
        user = await autenticar_estudiante(conn, datos.email, datos.contrasenna)
    except Exception as e:
        logger.error(f"Error de conexión a la base de datos durante login: {e}")
        return RedirectResponse(url="/inicio-sesion?error=1", status_code=status.HTTP_303_SEE_OTHER)
    if user is None:
        return RedirectResponse(url="/inicio-sesion?error=1", status_code=status.HTTP_303_SEE_OTHER)


    token = create_token(user["email"])
    response = RedirectResponse(url="/seleccionatuprofesor", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="token", value=token, httponly=True, samesite="lax", secure=True)  
    return response



@router.post("/login-admin")
async def login_admin(
    conn: ConnectionDep,
    datos: Annotated[LoginSchema, Form()],
):
    try:
        user = await inicio_sesion_admin(conn, datos.email, datos.contrasenna)
    except Exception as e:
        logger.error(f"Error de conexión a la base de datos durante login: {e}")
        return RedirectResponse(url="/administrador/iniciar-sesion?error=1", status_code=status.HTTP_303_SEE_OTHER)
    if user is None:
        return RedirectResponse(url="/administrador/iniciar-sesion?error=1", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/administrador", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/administrador/iniciar-sesion")
async def admin_login(request: Request):
    return templates.TemplateResponse(request=request, name="administrador-iniciar-sesion.html", context={})

@router.post("/nuevo-usuario")
async def nuevo_usuario(
    request: Request,
    conn: ConnectionDep,
    datos: Annotated[CrearEstudiante, Form()],
):
    if await existe_email(conn, datos.email):
        return templates.TemplateResponse(request=request, name="registrarse.html", context={"error": "El correo ya está registrado."})
    await registrar_estudiante(conn, datos.nombre, datos.email, datos.contrasenna, datos.grado)
    return templates.TemplateResponse(request=request, name="registrarse.html", context={"message": "Registrado exitosamente."})


@router.get("/seleccionatuprofesor", response_class=HTMLResponse)
async def read_seleccionatuprofesor(request: Request, conn: ConnectionDep, email: CurrentUserDep):
    profesores = await select_profesor(conn, email)
    nombre = await nombre_estudiante(conn, email)
    if not profesores or not nombre:
        return logger.warning(f"No se encontraron profesores para el estudiante con email: {email}")
    return templates.TemplateResponse(
        request=request,
        name="selectProfesor.html",
        context={"profesores": profesores, "nombre": nombre}
    )



@router.post("/seleccionatuprofesor")
async def seleccionar_profesor(request: Request, conn: ConnectionDep, email: CurrentUserDep, datos: Annotated[SeleccionProfesorSchema, Form()]):
    if not datos.maestro:
        nombre = await nombre_estudiante(conn, email)
        return templates.TemplateResponse(
            request=request,
            name="selectProfesor.html",
            context={"error": "Selecciona un profesor", "nombre": nombre}
        )
    nombre = await nombre_estudiante(conn, email)
    return templates.TemplateResponse(
        request=request,
        name="calification_plataform.html",
        context={"maestro": datos.maestro, "nombre": nombre["nombre"] if nombre else ""}
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


# ============ GESTIÓN DE ESTUDIANTES ============

@router.get("/gestionEstudiantes", response_class=HTMLResponse)
async def read_gestion_estudiantes(request: Request):
    return templates.TemplateResponse(request=request, name="gestionEstudiantes.html", context={})

@router.get("/gestionEstudiantes/nuevo", response_class=HTMLResponse)
async def nuevo_estudiante_form(request: Request):
    return templates.TemplateResponse(request=request, name="gestionEstudiantesForm.html", context={"titulo": "Nuevo Estudiante", "accion": "/gestionEstudiantes/nuevo"})

@router.post("/gestionEstudiantes/nuevo")
async def crear_estudiante(request: Request):
    return RedirectResponse(url="/gestionEstudiantes", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/gestionEstudiantes/{id}", response_class=HTMLResponse)
async def ver_estudiante(request: Request, id: int):
    return templates.TemplateResponse(request=request, name="gestionEstudiantesForm.html", context={"titulo": "Editar Estudiante", "accion": f"/gestionEstudiantes/{id}/editar"})

@router.get("/gestionEstudiantes/{id}/editar", response_class=HTMLResponse)
async def editar_estudiante_form(request: Request, id: int):
    return templates.TemplateResponse(request=request, name="gestionEstudiantesForm.html", context={"titulo": "Editar Estudiante", "accion": f"/gestionEstudiantes/{id}/editar"})

@router.post("/gestionEstudiantes/{id}/editar")
async def actualizar_estudiante(request: Request, id: int):
    return RedirectResponse(url="/gestionEstudiantes", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/gestionEstudiantes/{id}/eliminar")
async def eliminar_estudiante(request: Request, id: int):
    return RedirectResponse(url="/gestionEstudiantes", status_code=status.HTTP_303_SEE_OTHER)


# ============ GESTIÓN DE PROFESORES ============

@router.get("/gestionProfesores/nuevo", response_class=HTMLResponse)
async def nuevo_profesor_form(request: Request):
    return templates.TemplateResponse(request=request, name="gestionProfesoresForm.html", context={"titulo": "Nuevo Profesor", "accion": "/gestionProfesores/nuevo"})

@router.post("/gestionProfesores/nuevo")
async def crear_profesor(request: Request):
    return RedirectResponse(url="/gestionProfesores", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/gestionProfesores/{id}", response_class=HTMLResponse)
async def ver_profesor(request: Request, id: int):
    return templates.TemplateResponse(request=request, name="gestionProfesoresInformacion.html", context={})

@router.get("/gestionProfesores/{id}/editar", response_class=HTMLResponse)
async def editar_profesor_form(request: Request, id: int):
    return templates.TemplateResponse(request=request, name="gestionProfesoresForm.html", context={"titulo": "Editar Profesor", "accion": f"/gestionProfesores/{id}/editar"})

@router.post("/gestionProfesores/{id}/editar")
async def actualizar_profesor(request: Request, id: int):
    return RedirectResponse(url="/gestionProfesores", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/gestionProfesores/{id}/editar-grado", response_class=HTMLResponse)
async def editar_grado_profesor_form(request: Request, id: int):
    return templates.TemplateResponse(request=request, name="gestionProfesoresForm.html", context={"titulo": "Cambiar Grado del Profesor", "accion": f"/gestionProfesores/{id}/editar-grado"})

@router.post("/gestionProfesores/{id}/editar-grado")
async def actualizar_grado_profesor(request: Request, id: int):
    return RedirectResponse(url=f"/gestionProfesores/{id}", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/gestionProfesores/{id}/eliminar")
async def eliminar_profesor(request: Request, id: int):
    return RedirectResponse(url="/gestionProfesores", status_code=status.HTTP_303_SEE_OTHER)


# ============ GESTIÓN DE GRADOS ============

@router.get("/gestionGrados", response_class=HTMLResponse)
async def read_gestion_grados(request: Request):
    return templates.TemplateResponse(request=request, name="gestionGrados.html", context={})

@router.get("/gestionGrados/nuevo", response_class=HTMLResponse)
async def nuevo_grado_form(request: Request):
    return templates.TemplateResponse(request=request, name="gestionGradosForm.html", context={"titulo": "Nuevo Grado", "accion": "/gestionGrados/nuevo"})

@router.post("/gestionGrados/nuevo")
async def crear_grado(request: Request):
    return RedirectResponse(url="/gestionGrados", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/gestionGrados/{id}/editar", response_class=HTMLResponse)
async def editar_grado_form(request: Request, id: int):
    return templates.TemplateResponse(request=request, name="gestionGradosForm.html", context={"titulo": "Editar Grado", "accion": f"/gestionGrados/{id}/editar"})

@router.post("/gestionGrados/{id}/editar")
async def actualizar_grado(request: Request, id: int):
    return RedirectResponse(url="/gestionGrados", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/gestionGrados/{id}/eliminar")
async def eliminar_grado(request: Request, id: int):
    return RedirectResponse(url="/gestionGrados", status_code=status.HTTP_303_SEE_OTHER)


# ============ HISTORIAL DE CAMBIOS ============

@router.get("/historialCambios", response_class=HTMLResponse)
async def read_historial_cambios(request: Request):
    return templates.TemplateResponse(request=request, name="historialCambios.html", context={})


@router.post("/calificaElProfesor")
async def enviar_calificacion(
    request: Request,
    conn: ConnectionDep,
    email: CurrentUserDep,
    datos: Annotated[CalificacionSchema, Form()]
):
    try:
        await registrar_calificacion(
            conn, email, datos.maestro,
            datos.explicationsTopics, datos.actitudinal, datos.classActivity
        )
    except Exception as e:
        logger.error(f"Error al registrar calificación: {e}")
        nombre = await nombre_estudiante(conn, email)
        return templates.TemplateResponse(
            request=request,
            name="calification_plataform.html",
            context={"maestro": datos.maestro, "nombre": nombre["nombre"] if nombre else "", "error": "Error al registrar la calificación"}
        )
    nombre = await nombre_estudiante(conn, email)
    return templates.TemplateResponse(
        request=request,
        name="certificado.html",
        context={"nombre": nombre["nombre"] if nombre else ""}
    )


@router.get("/Agradecimiento", response_class=HTMLResponse)
async def read_agradecimiento(request: Request, conn: ConnectionDep, email: CurrentUserDep):
    nombre = await nombre_estudiante(conn, email)
    return templates.TemplateResponse(
        request=request,
        name="certificado.html",
        context={"nombre": nombre["nombre"] if nombre else ""}
    )
