async def inicio_sesion(conn, email: str, contrasenna: str) -> dict | None:
    row = await conn.fetchrow(
        "SELECT email, contrasenna FROM estudiantes WHERE email = $1 AND contrasenna = $2",
        email, contrasenna
    )
    return dict(row) if row else None

async def existe_email(conn, email: str) -> bool:
    row = await conn.fetchrow("SELECT 1 FROM estudiantes WHERE email = $1", email)
    return row is not None

async def registrar_estudiante(conn, nombre: str, email: str, contrasenna: str, grado: int) -> None:
    await conn.execute(
        "INSERT INTO estudiantes (nombre, contrasenna, email, id_grado) VALUES ($1, $2, $3, $4)",
        nombre, contrasenna, email, grado
    )

async def select_profesor(conn)-> list[dict]:
    rows = await conn.fetch("""
SELECT maestros.nombre FROM inscripciones 
JOIN asignaciones ON inscripciones.id_asignacion = asignaciones.id
JOIN estudiantes ON inscripciones.id_estudiante = estudiantes.id
JOIN maestros ON asignaciones.id_profesor = maestros.id
WHERE inscripciones.ya_voto = false
    """)
    return [dict(row) for row in rows] if rows else None
