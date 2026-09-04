async def inicio_sesion(conn, email: str, contrasenna: str) -> dict | None:
    row = await conn.fetchrow(
        "SELECT email, contrasenna FROM estudiantes WHERE email = $1 AND contrasenna = $2",
        email, contrasenna,
    )
    return dict(row) if row else None

async def registrarse_correo(conn) -> dict:
    rows = await conn.fetch("SELECT email FROM estudiantes ")
    return dict(rows) if rows else None

async def registrarse(conn, nombre: str) -> dict:
    rows = await conn.fetch("INSERT INTO estudiantes (nombre) VALUES ($1) RETURNING *", nombre)
    return dict(rows) if rows else None

async def select_profesor(conn)-> list[dict]:
    rows = await conn.fetch("""
SELECT maestros.nombre FROM inscripciones 
JOIN asignaciones ON inscripciones.id_asignacion = asignaciones.id
JOIN estudiantes ON inscripciones.id_estudiante = estudiantes.id
JOIN maestros ON asignaciones.id_profesor = maestros.id
WHERE inscripciones.ya_voto = false
    """)
    return [dict(row) for row in rows] if rows else None
