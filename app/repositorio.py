async def inicio_sesion(conn, email: str, contrasenna: str) -> dict | None:
    row = await conn.fetchrow(
        "SELECT email, contrasenna FROM estudiantes WHERE email = $1 AND contrasenna = $2",
        email, contrasenna
    )
    return dict(row) if row else None

async def inicio_sesion_admin(conn, email: str, contrasenna: str) -> dict | None:
    row = await conn.fetchrow(
        "SELECT email, contrasenna FROM administradores WHERE email = $1 AND contrasenna = $2",
        email, contrasenna
    )
    return dict(row) if row else None

async def existe_email(conn, email: str) -> bool:
    row = await conn.fetchrow("SELECT 1 FROM estudiantes WHERE email = $1", email)
    return row is not None

async def registrar_estudiante(conn, nombre: str, email: str, contrasenna: str, grado: int) -> None:
    async with conn.transaction():
        estudiante_id = await conn.fetchval(
            """
            INSERT INTO estudiantes (nombre, contrasenna, email, id_grado)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            """,
            nombre, contrasenna, email, grado
        )

        await conn.execute(
            """
            INSERT INTO inscripciones (id_estudiante, id_asignacion)
            SELECT $1, asignaciones.id
            FROM asignaciones
            JOIN periodos ON periodos.id = asignaciones.id_periodo
            WHERE asignaciones.id_grado = $2
                AND periodos.estado = 'abierto'
            """,
            estudiante_id, grado
        )
async def select_profesor(conn, email: str) -> list[dict]:
    rows = await conn.fetch("""
SELECT DISTINCT maestros.nombre
FROM asignaciones
JOIN maestros ON maestros.id = asignaciones.id_profesor
JOIN estudiantes ON estudiantes.id_grado = asignaciones.id_grado
LEFT JOIN inscripciones
    ON inscripciones.id_asignacion = asignaciones.id
    AND inscripciones.id_estudiante = estudiantes.id
WHERE estudiantes.email = $1
    AND (inscripciones.ya_voto IS NULL OR inscripciones.ya_voto = false)
    """, email)
    return [dict(row) for row in rows] if rows else []

async def nombre_estudiante(conn, email: str) -> dict | None:
    row = await conn.fetchrow(
        "SELECT nombre FROM estudiantes WHERE email = $1",
        email
    )
    return dict(row) if row else None