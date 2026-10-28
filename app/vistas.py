# ============================================================================
# vistas.py — Endpoints HTTP principales (FastAPI routes)
# ============================================================================
# Este archivo define todas las rutas HTTP expuestas por la aplicación.
# Actúa como la capa de presentación: recibe requests, invoca lógica de
# negocio en repositorio.py, y retorna HTML renderizado con Jinja2.
#
# Patrón general de cada endpoint:
#   1. Extraer datos del request (cookies, query params, body/Form data)
#   2. Invocar funciones de app/repositorio.py para acceso a la BD
#   3. Renderizar una plantilla HTML con Jinja2 o redirigir
#
# Dependencias inyectadas por app/dependencias.py:
#   - ConnectionDep: conexión asyncpg desde el pool central
#   - CurrentUserDep: email extraído y verificado del cookie JWT
#
# Schemas de validación de datos en app/esquemas.py:
#   - LoginSchema, CrearEstudiante, CrearMaestro, GuardarEstudiante,
#     CalificacionSchema, SeleccionProfesorSchema
#
# Token JWT en app/seguridad.py:
#   - create_token(): firma un token HS256 con el email del usuario
# ============================================================================

from typing import Annotated

from fastapi import Depends, Request, Form, status, APIRouter
from fastapi.responses import RedirectResponse, PlainTextResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from loguru import logger
from app.dependencias import ConnectionDep, CurrentUserDep
from app.repositorio import (
    inicio_sesion as autenticar_estudiante,
    registrar_maestro, registrar_estudiante, existe_email,
    inicio_sesion_admin, select_profesor, nombre_estudiante,
    registrar_calificacion, estadisticas_admin, detalle_por_grado,
    detalle_estudiantes, detalle_por_estudiantes, actualizarectudiante,
    eliminar_estudiante, obtener_todos_los_profesores,
    eliminar_grado as eliminar_grado_bd, listar_grados,
    listar_materias, listar_periodos,
    detalle_por_profesor, actualizar_profesor,
    guardar_maestro,
)
from app.esquemas import (
    CrearEstudiante, CrearMaestro, GuardarEstudiante, GuardarProfesor,
    LoginSchema, CalificacionSchema, SeleccionProfesorSchema,
)
from app.seguridad import create_token
from fastapi.responses import Response

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# ============================================================================
# RUTAS PÚBLICAS (sin autenticación)
# ============================================================================

@router.get("/", response_class=HTMLResponse)
async def inicio(request: Request):
    """Página principal de la aplicación: muestra la landing page (inicio.html).
    No requiere autenticación ni datos adicionales."""
    return templates.TemplateResponse(request=request, name="inicio.html", context={})


# ============ INICIO DE SESIÓN ============

@router.get("/inicio-sesion", response_class=HTMLResponse)
async def inicio_sesion(request: Request, error: str = None):
    """Muestra el formulario de inicio de sesión de estudiante (index.html).
    Si se pasó un parámetro `error` en la URL, lo pasa a la plantilla para
    mostrar un mensaje de error (credenciales inválidas, etc.)."""
    return templates.TemplateResponse(request=request, name="index.html", context={"error": error})


@router.get("/registrarse", response_class=HTMLResponse)
async def registrarse(request: Request):
    """Muestra el formulario de registro de nuevo estudiante (registrarse.html)."""
    return templates.TemplateResponse(request=request, name="registrarse.html", context={})




# ============ AUTENTICACIÓN (POST) ============

@router.post("/login")
async def login(
    conn: ConnectionDep,
    datos: Annotated[LoginSchema, Form()]
):
    """Autentica un estudiante mediante email + contraseña recibidos por formulario.
    
    1. Busca las credenciales en la BD usando `autenticar_estudiante()` de repositorio.py.
    2. Si son válidas, firma un JWT con el email del estudiante y lo almacena en una cookie
       HTTP-only (samesite=lax, secure=True) para mantener la sesión.
    3. Redirige a la página de selección de profesor.
    
    Si hay error de BD o credenciales inválidas, redirige de vuelta al formulario con error=1.
    """
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
    """Autentica un administrador mediante email + contraseña.
    
    Similar a login() pero para el panel de administración. Si las credenciales
    son válidas, emite un JWT y redirige a /administrador.
    """
    try:
        user = await inicio_sesion_admin(conn, datos.email, datos.contrasenna)
    except Exception as e:
        logger.error(f"Error de conexión a la base de datos durante login: {e}")
        return RedirectResponse(url="/administrador/iniciar-sesion?error=1", status_code=status.HTTP_303_SEE_OTHER)
    if user is None:
        return RedirectResponse(url="/administrador/iniciar-sesion?error=1", status_code=status.HTTP_303_SEE_OTHER)
    
    token = create_token(user["email"])
    response = RedirectResponse(url="/administrador", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="token", value=token, httponly=True, samesite="lax", secure=True)  
    return response



@router.get("/administrador/iniciar-sesion")
async def admin_login(request: Request):
    """Muestra el formulario de inicio de sesión del administrador (administrador-iniciar-sesion.html)."""
    return templates.TemplateResponse(request=request, name="administrador-iniciar-sesion.html", context={})

# ============ REGISTRO DE USUARIOS (POST) ============

@router.post("/nuevo-usuario")
async def nuevo_usuario(
    request: Request,
    conn: ConnectionDep,
    datos: Annotated[CrearEstudiante, Form()],
):
    """Registra un nuevo estudiante a partir de los datos del formulario.
    
    1. Verifica que el email no exista ya en la BD usando `existe_email()` de repositorio.py.
    2. Si el email está libre, invoca `registrar_estudiante()` para crear el registro.
    3. Siempre re-muestra `registrarse.html` con un mensaje de éxito o error.
    
    Nota: También tiene un endpoint paralelo `/nuevo-maestro` para registrar maestros.
    """
    if await existe_email(conn, datos.email):
        return templates.TemplateResponse(request=request, name="registrarse.html", context={"error": "El correo ya está registrado."})
    await registrar_estudiante(conn, datos.nombre, datos.email, datos.contrasenna, datos.grado)
    return templates.TemplateResponse(request=request, name="registrarse.html", context={"message": "Registrado exitosamente."})

@router.post("/nuevo-maestro")
async def nuevo_maestro(
    request: Request,
    conn: ConnectionDep,
    datos: Annotated[CrearMaestro, Form()],
):
    """Registra un nuevo maestro a partir de los datos del formulario.
    
    Similar a `nuevo_usuario()`: verifica unicidad de email con `existe_email()`
    y luego invoca `registrar_maestro()` de repositorio.py. Re-muestra el
    mismo formulario con mensaje de éxito o error.
    """
    if await existe_email(conn, datos.email):
        return templates.TemplateResponse(request=request, name="registrarse.html", context={"error": "El correo ya está registrado."})
    await registrar_maestro(conn, datos.nombre, datos.email, datos.contrasenna, datos.especialidad)
    return templates.TemplateResponse(request=request, name="registrarse.html", context={"message": "Registrado exitosamente."})


# ============ SELECCIÓN / CALIFICACIÓN DE PROFESOR ============

@router.get("/seleccionatuprofesor", response_class=HTMLResponse)
async def read_seleccionatuprofesor(request: Request, conn: ConnectionDep, email: CurrentUserDep):
    """Muestra la página de selección de profesor al estudiante logueado.
    
    1. Obtén la lista de profesores asignados al grado del estudiante vía `select_profesor()`.
    2. Obtén el nombre del estudiante vía `nombre_estudiante()`.
    3. Renderiza `selectProfesor.html` con ambos datos.
    
    Si no hay profesores o nombre, loguea un warning y retorna vacío.
    """
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
    """Procesa la selección de profesor por parte del estudiante.
    
    1. Valida que se haya seleccionado un profesor (`datos.maestro`).
    2. Si no hay selección, re-muestra el formulario con error.
    3. Si hay selección, avanza a la página de calificación `calification_plataform.html`
       mostrando el profesor elegido.
    """
    if not datos.maestro:
        nombre = await nombre_estudiante(conn, email)
        return templates.TemplateResponse(
            request=request,
            name="selectProfesor.html",
            context={"error": "Selecciona un profesor", "nombre": nombre}
        )
    nombre = await nombre_estudiante(conn, email)
    partes = datos.maestro.split("|")
    maestro_solo = partes[0].strip()
    id_materia = int(partes[1]) if len(partes) > 1 else datos.id_materia
    return templates.TemplateResponse(
        request=request,
        name="calification_plataform.html",
        context={"maestro": maestro_solo, "nombre": nombre["nombre"] if nombre else "", "id_materia": id_materia}
    )

# ============ DASHBOARD ADMINISTRADOR ============

@router.get("/centroEstadistico", response_class=HTMLResponse)
async def read_centro_estadistico(request: Request, conn: ConnectionDep):
    """Muestra el centro estadístico del panel de administración.
    
    1. Compila todas las métricas generales vía `estadisticas_admin()` de repositorio.py.
    2. Calcula estadísticas detalladas por grado vía `detalle_por_grado()` (promedios,
       mejor profesor por grado, estado del periodo).
    3. Renderiza `centroEstadistico.html` con ambos conjuntos de datos fusionados.
    """
    contexto = await estadisticas_admin(conn)
    dpg = await detalle_por_grado(conn)
    return templates.TemplateResponse(
        request=request, name="centroEstadistico.html",
        context={**contexto, "dpg": dpg}
    )


@router.get("/administrador", response_class=HTMLResponse)
async def read_administrador(request: Request, email: CurrentUserDep, conn: ConnectionDep):
    """Renderiza el dashboard principal del administrador (administradorMain.html).
    
    1. Verifica que el usuario esté autenticado (Cookie JWT válida). Si no, redirige
       al formulario de login de administrador.
    2. Compila métricas generales con `estadisticas_admin()`.
    3. Renderiza el dashboard con esas métricas.
    """
    contexto = await estadisticas_admin(conn)
    if not email:
        return RedirectResponse(
            url="/administrador/iniciar-sesion",
            status_code=status.HTTP_303_SEE_OTHER
        )
    return templates.TemplateResponse(
        request=request, name="administradorMain.html", context=contexto
    )


@router.get("/gestionGrados", response_class=HTMLResponse)
async def read_gestion_grados(request: Request, conn: ConnectionDep):
    """Muestra la página de gestión de grados con las métricas generales.
    
    1. Obtiene estadísticas generales con `estadisticas_admin()`.
    2. Obtiene la lista real de grados con `listar_grados()`.
    3. Renderiza `gestionGrados.html` con esas métricas y el listado.
    
    Nota: Este endpoint tiene una versión duplicada sin contexto en la sección
    de CRUD de grados (línea 341). Esta es la versión completa que recibe
    ConnectionDep y pasa estadísticas al template.
    """
    contexto = await estadisticas_admin(conn)
    contexto["grados"] = await listar_grados(conn)
    return templates.TemplateResponse(
        request=request, name="gestionGrados.html", context=contexto
    )


@router.get("/gestionGrados/nuevo", response_class=HTMLResponse)
async def read_gestion_grados_nuevo(request: Request):
    """Muestra el formulario vacío para crear un nuevo grado."""
    return templates.TemplateResponse(
        request=request, name="gestionGradoNuevo.html", context={}
    )


@router.get("/gestionProfesores", response_class=HTMLResponse)
async def read_gestion_profesores(request: Request, conn: ConnectionDep):
    """Muestra la página de gestión de profesores con datos reales de la BD.
    
    Obtiene todos los profesores, su grado asignado, promedio de evaluación
    y estado (Activo/Alerta) desde PostgreSQL.
    """
    try:
        teachers = await obtener_todos_los_profesores(conn)
        logger.info(f"gestionProfesores cargado con {len(teachers)} profesores")
        return templates.TemplateResponse(
            request=request, name="gestionProfesores.html", context={"teachers": teachers}
        )
    except Exception as e:
        logger.error(f"Error en gestionProfesores: {type(e).__name__}: {e}")
        return HTMLResponse(
            content="Error al cargar los profesores. Intente de nuevo.",
            status_code=500,
        )


async def _form_nuevo_profesor(request: Request, conn: ConnectionDep, error: str | None = None):
    """Renderiza el formulario de nuevo profesor con las listas de la BD.

    Carga materias, grados y periodos desde PostgreSQL y los pasa al template
    `gestionProfesoresNuevo.html`. El parámetro `error` permite re-renderizar
    el mismo formulario mostrando un mensaje de validación (lo usa el POST).
    """
    materias = await listar_materias(conn)
    grados = await listar_grados(conn)
    periodos = await listar_periodos(conn)
    return templates.TemplateResponse(
        request=request,
        name="gestionProfesoresNuevo.html",
        context={
            "materias": materias,
            "grados": grados,
            "periodos": periodos,
            "error": error,
        },
    )


@router.get("/gestionProfesores/nuevo", response_class=HTMLResponse)
async def read_gestion_profesores_nuevo(request: Request, conn: ConnectionDep):
    """Muestra el formulario para crear un nuevo profesor.

    Carga materias, grados y periodos desde la BD para poblar los chips
    de selección del formulario.
    """
    return await _form_nuevo_profesor(request, conn)


# ============ HTMX: chips de selección ============

@router.post("/gestionProfesores/nuevo/chip")
async def chip_materia_grado(
    request: Request,
    tipo: Annotated[str, Form()],
    id: Annotated[int, Form()],
    nombre: Annotated[str, Form()],
    seleccionado: Annotated[bool, Form()],
):
    """Alterna el estado seleccionado de un chip de materia o grado.

    Recibe el chip actual por Form data y devuelve el mismo chip con el
    estado invertido para que HTMX lo reemplace en el DOM.
    """
    return templates.TemplateResponse(
        request=request,
        name="chip.html",
        context={"tipo": tipo, "id": id, "nombre": nombre, "seleccionado": not seleccionado},
    )


@router.post("/gestionProfesores/nuevo/periodo")
async def chip_periodo(request: Request, conn: ConnectionDep, id: Annotated[int, Form()]):
    """Devuelve la lista completa de periodos con el periodo activo resaltado.

    Recarga los periodos desde la BD y los renderiza en `periodosChips.html`
    marcando como activo el periodo recibido por Form data.
    """
    periodos = await listar_periodos(conn)
    return templates.TemplateResponse(
        request=request,
        name="periodosChips.html",
        context={"periodos": periodos, "activo": id},
    )


@router.get("/configuracion", response_class=HTMLResponse)
async def configuracion(request: Request):
    """Muestra la página de configuración del sistema."""
    return templates.TemplateResponse(
        request=request, name="configuracion.html", context={}
    )


# ============ GESTIÓN DE ESTUDIANTES ============

@router.get("/gestionEstudiantes", response_class=HTMLResponse)
async def read_gestion_estudiantes(request: Request, conn: ConnectionDep):
    """Muestra la página de gestión de estudiantes con la lista completa de estudiantes registrados.

    Obtiene los datos de estudiantes desde la base de datos y los pasa al template.
    """
    estudiantes = await detalle_estudiantes(conn)
    return templates.TemplateResponse(request=request, name="gestionEstudiantes.html", context={"estudiantes": estudiantes})

@router.get("/gestionEstudiantes/cancelar", response_class=HTMLResponse)
async def cancelar_edicion(request: Request):
    """Cancela la edición de un estudiante y redirige a la lista principal.

    Usado por HTMX para cancelar acciones en curso y volver al listado.
    """
    return Response(status_code=303, headers={"HX-Redirect": "/gestionEstudiantes"})
    

@router.get("/gestionEstudiantes/nuevo")
async def crear_estudiante_get(request: Request):
    """Muestra el formulario vacío para registrar un nuevo estudiante."""
    return templates.TemplateResponse(request=request, name="gestionEstudiantesNuevo.html", context={})

@router.post("/gestionEstudiantes/{id}/nuevo")
async def crear_estudiante(request: Request):
    """Procesa la creación de un nuevo estudiante a través del formulario.

    Stub: recibe los datos del formulario y redirige al listado de estudiantes.
    La lógica real de insercción debe implementarse aquí.
    """
    return RedirectResponse(url="/gestionEstudiantes", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/gestionEstudiantes/{id}", response_class=HTMLResponse)
async def ver_estudiante(request: Request, id: int):
    """Muestra el formulario de edición para un estudiante específico.

    Renderiza el template con el título "Editar Estudiante" y la acción del formulario
    predefinida con el ID del estudiante.
    """
    return templates.TemplateResponse(request=request, name="gestionEstudiantesForm.html", context={"titulo": "Editar Estudiante", "accion": f"/gestionEstudiantes/{id}/editar"})

@router.get("/gestionEstudiantes/{id_estudiante}/editar", response_class=HTMLResponse)
async def editar_estudiante_form(request: Request, conn: ConnectionDep, id_estudiante: int):
    """Muestra el formulario de edición con los datos actuales del estudiante.

    Obtiene los datos del estudiante desde la base de datos y los pasa al template
    para que el usuario pueda modificarlos.
    """
    estudiante = await detalle_por_estudiantes(conn, id_estudiante)
    return templates.TemplateResponse(request=request, name="gestionEstudianteForm_editar.html", context={"estudiante": estudiante})

@router.put("/gestionEstudiantes/{id_estudiante}/guardar")
async def actualizar_estudiante(request: Request,conn: ConnectionDep, datos: Annotated[GuardarEstudiante, Form()], id_estudiante: int):
    """Procesa la actualización de los datos de un estudiante existente.

    Recibe los datos validados por el schema GuardarEstudiante, los actualiza en la
    base de datos y redirige al listado si la operación fue exitosa.
    """
    estudiante = await actualizarectudiante(conn, id_estudiante, datos.nombre, datos.email, datos.grado)
    if estudiante:
        return Response(status_code=303, headers={"HX-Redirect": "/gestionEstudiantes"})



@router.delete("/gestionEstudiantes/{id_estudiante}/eliminar")
async def eliminar_estudiante_ruta(request: Request, id_estudiante: int, conn: ConnectionDep):
    """Elimina un estudiante de la base de datos por su ID.

    Recibe el ID del estudiante, lo elimina y redirige al listado si la operación
    fue exitosa.
    """
    estudiantes = await eliminar_estudiante(conn, id_estudiante)
    if estudiantes:
        return Response(status_code=200, headers={"HX-Redirect": "/gestionEstudiantes"})
    


# ============ GESTIÓN DE PROFESORES ============
# CRUD para administrar el listado de profesores registrados.
# Todos estos endpoints son stubs (sin lógica real): solo renderizan templates
# con datos genéricos o redirigen. No acceden a la base de datos ni validan datos.

@router.post("/gestionProfesores/nuevo")
async def crear_profesor(
    request: Request,
    conn: ConnectionDep,
    nombre: Annotated[str, Form(min_length=1, max_length=60)],
    materias: Annotated[list[int], Form()] = [],
    grados: Annotated[list[int], Form()] = [],
    periodo: Annotated[int | None, Form()] = None,
):
    """Crea un nuevo profesor a partir de los datos del formulario.

    Valida que se haya seleccionado al menos una materia, un grado y un periodo;
    si falta algo, re-renderiza el formulario con mensaje de error. Con datos
    válidos guarda el profesor vía `guardar_maestro` (maestro + asignaciones +
    inscripciones) y redirige al listado; si la BD falla, re-renderiza el
    formulario con mensaje de error.
    """
    if not materias or not grados or periodo is None:
        return await _form_nuevo_profesor(
            request, conn, error="Selecciona al menos una materia, un grado y un periodo."
        )
    try:
        await guardar_maestro(conn, nombre.strip(), materias, grados, periodo)
        return RedirectResponse(url="/gestionProfesores", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        logger.error(f"Error guardando profesor '{nombre}': {type(e).__name__}: {e}")
        return await _form_nuevo_profesor(
            request, conn, error="No se pudo guardar el profesor. Verifica los datos e intenta de nuevo."
        )

@router.get("/gestionProfesores/cancelar", response_class=HTMLResponse)
async def cancelar_edicion_profesor(request: Request):
    """Cancela la edición de un profesor y redirige a la lista principal.

    Usado por HTMX para cancelar la edición inline y volver al listado.
    Debe declararse ANTES de GET /gestionProfesores/{id} para que {id: int}
    no capture "cancelar" y devuelva 422.
    """
    return Response(status_code=303, headers={"HX-Redirect": "/gestionProfesores"})

@router.get("/gestionProfesores/{id}", response_class=HTMLResponse)
async def ver_profesor(request: Request, id: int):
    """Muestra la página de información de un profesor por ID.

    Stub: renderiza `gestionProfesoresInformacion.html` pero no pasa datos
    del profesor (context vacío).
    """
    return templates.TemplateResponse(request=request, name="gestionProfesoresInformacion.html", context={})

@router.get("/gestionProfesores/{id}/editar", response_class=HTMLResponse)
async def editar_profesor_form(request: Request, conn: ConnectionDep, id: int):
    """Muestra el formulario de edición inline (htmx) de un profesor por ID.

    Carga los datos reales del profesor desde la BD y renderiza el parcial
    `gestionProfesoresForm_editar.html` (una <tr> editable que reemplaza la
    fila de la tabla vía hx-swap="outerHTML"). Si el ID no existe, responde
    con HX-Redirect al listado para no dejar una fila rota.
    """
    profesor = await detalle_por_profesor(conn, id)
    if profesor is None:
        return Response(status_code=200, headers={"HX-Redirect": "/gestionProfesores"})
    return templates.TemplateResponse(request=request, name="gestionProfesoresForm_editar.html", context={"profesor": profesor})

@router.put("/gestionProfesores/{id}/guardar")
async def guardar_profesor(request: Request, conn: ConnectionDep, datos: Annotated[GuardarProfesor, Form()], id: int):
    """Actualiza el nombre de un profesor existente (edición inline htmx).

    Recibe los datos validados por el schema GuardarProfesor, actualiza el
    nombre en la BD y responde con HX-Redirect al listado (patrón de
    actualizar_estudiante).
    """
    await actualizar_profesor(conn, id, datos.nombre)
    return Response(status_code=303, headers={"HX-Redirect": "/gestionProfesores"})

@router.get("/gestionProfesores/{id}/editar-grado", response_class=HTMLResponse)
async def editar_grado_profesor_form(request: Request, id: int):
    """Muestra el formulario para cambiar el grado de un profesor.

    Stub: renderiza `gestionProfesoresForm.html` con título específico para cambio
    de grado, pero sin datos reales.
    """
    return templates.TemplateResponse(request=request, name="gestionProfesoresForm.html", context={"titulo": "Cambiar Grado del Profesor", "accion": f"/gestionProfesores/{id}/editar-grado"})

@router.post("/gestionProfesores/{id}/editar-grado")
async def actualizar_grado_profesor(request: Request, id: int):
    """Actualiza el grado de un profesor existente.

    Stub: no extrae ni valida datos del request. Redirige a la página de
    información del profesor.
    """
    return RedirectResponse(url=f"/gestionProfesores/{id}", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/gestionProfesores/{id}/eliminar")
async def eliminar_profesor(request: Request, id: int):
    """Elimina un profesor por ID.

    Stub: no realiza ninguna operación real. Simplemente redirige al listado.
    """
    return RedirectResponse(url="/gestionProfesores", status_code=status.HTTP_303_SEE_OTHER)


# ============ GESTIÓN DE GRADOS ============
# CRUD para administrar los grados académicos (ej: "1° A", "2° B", etc.).
# Todos estos endpoints son stubs: no acceden a la BD ni procesan datos.
# Nota: Existe una segunda función `read_gestion_grados()` en la línea 261 con
# lógica real (estadísticas + ConnectionDep); esta es una versión duplicada sin contexto.



@router.get("/gestionGrados/nuevo", response_class=HTMLResponse)
async def nuevo_grado_form(request: Request):
    """Muestra el formulario vacío para crear un nuevo grado.

    Stub: renderiza `gestionGradosForm.html` con título y acción predefinidos.
    No valida ni carga datos previos.
    """
    return templates.TemplateResponse(request=request, name="gestionGradosForm.html", context={"titulo": "Nuevo Grado", "accion": "/gestionGrados/nuevo"})

@router.post("/gestionGrados/nuevo")
async def crear_grado(request: Request):
    """Crea un nuevo grado a partir de los datos del formulario.

    Stub: no extrae ni valida datos del request. Simplemente redirige al listado.
    """
    return RedirectResponse(url="/gestionGrados", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/gestionGrados/{id}/editar", response_class=HTMLResponse)
async def editar_grado_form(request: Request, id: int):
    """Muestra el formulario de edición de un grado por ID.

    Stub: renderiza `gestionGradosForm.html` con título y acción predefinidos.
    """
    return templates.TemplateResponse(request=request, name="gestionGradosForm.html", context={"titulo": "Editar Grado", "accion": f"/gestionGrados/{id}/editar"})

@router.post("/gestionGrados/{id}/editar")
async def actualizar_grado(request: Request, id: int):
    """Actualiza los datos de un grado existente.

    Stub: no extrae ni procesa datos del request. Simplemente redirige al listado.
    """
    return RedirectResponse(url="/gestionGrados", status_code=status.HTTP_303_SEE_OTHER)

@router.delete("/gestionGrados/{id}/eliminar")
async def eliminar_grado(request: Request, id: int, conn: ConnectionDep):
    """Elimina un grado por ID, solo si no tiene estudiantes ni asignaciones.

    Si el grado tiene estudiantes o asignaciones asociadas, NO se elimina
    y simplemente se redirige al listado (el grado sigue apareciendo).
    """
    eliminado = await eliminar_grado_bd(conn, id)
    if eliminado:
        return Response(status_code=200, headers={"HX-Redirect": "/gestionGrados"})
    return RedirectResponse(url="/gestionGrados", status_code=status.HTTP_303_SEE_OTHER)


# ============ HISTORIAL DE CAMBIOS ============
# Visualización del historial de acciones realizadas en la plataforma.

@router.get("/historialCambios", response_class=HTMLResponse)
async def read_historial_cambios(request: Request):
    """Muestra la página de historial de cambios realizados.

    Stub: renderiza `historialCambios.html` con contexto vacío.
    No carga datos del historial.
    """
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
            datos.explication, datos.actitudinal, datos.class_activity,datos.id_materia
        )
    except Exception as e:
        logger.error(f"Error al registrar calificación: {e}")
        nombre = await nombre_estudiante(conn, email)
        return templates.TemplateResponse(
            request=request,
            name="calification_plataform.html",
            context={"maestro": datos.maestro, "nombre": nombre["nombre"] if nombre else "", "id_materia": datos.id_materia, "error": "Error al registrar la calificación"}
        )
    nombre = await nombre_estudiante(conn, email)
    return templates.TemplateResponse(
        request=request,
        name="certificado.html",
        context={"nombre": nombre["nombre"] if nombre else ""}
    )


@router.get("/Agradecimiento", response_class=HTMLResponse)
async def read_agradecimiento(request: Request, conn: ConnectionDep, email: CurrentUserDep):
    """Muestra la página de agradecimiento/certificado tras calificar un profesor.

    1. Obtén el nombre del estudiante autenticado vía `nombre_estudiante()`
       de repositorio.py usando el email del JWT.
    2. Renderiza `certificado.html` con el nombre del estudiante.
    """
    nombre = await nombre_estudiante(conn, email)
    return templates.TemplateResponse(
        request=request,
        name="certificado.html",
        context={"nombre": nombre["nombre"] if nombre else ""}
    )
