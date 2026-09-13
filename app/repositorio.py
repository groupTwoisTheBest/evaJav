from app.seguridad import hash_password, verify_password


async def inicio_sesion(conn, email: str, contrasenna: str) -> dict | None:
    row = await conn.fetchrow(
        "SELECT email, contrasenna FROM estudiantes WHERE email = $1",
        email
    )
    if row and verify_password(contrasenna, row["contrasenna"]):
        return dict(row)
    return None

async def inicio_sesion_admin(conn, email: str, contrasenna: str) -> dict | None:
    row = await conn.fetchrow(
        "SELECT email, contrasenna FROM administradores WHERE email = $1",
        email
    )
    if row and verify_password(contrasenna, row["contrasenna"]):
        return dict(row)
    return None

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
            nombre, hash_password(contrasenna), email, grado
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


async def registrar_calificacion(
    conn, email: str, profesor: str,
    explication: str, actitudinal: str, class_activity: str
) -> None:
    mapa = {"Malo": 1, "Regular": 2, "Bien": 3, "Excelente": 4}
    profesor = profesor.strip()

    async with conn.transaction():
        asignaciones = await conn.fetch("""
            SELECT a.id
            FROM asignaciones a
            JOIN maestros m ON m.id = a.id_profesor
            JOIN estudiantes e ON e.id_grado = a.id_grado
            JOIN periodos p ON p.id = a.id_periodo
            JOIN inscripciones i ON i.id_asignacion = a.id AND i.id_estudiante = e.id
            WHERE e.email = $1 AND m.nombre = $2
                AND p.estado = 'abierto' AND i.ya_voto = false
        """, email, profesor)

        if not asignaciones:
            raise ValueError("No se encontró la asignación para esta evaluación")

        for a in asignaciones:
            await conn.execute("""
                INSERT INTO evaluaciones (id_asignacion, actitudinal, actividades, metodologia)
                VALUES ($1, $2, $3, $4)
            """, a["id"], mapa[actitudinal], mapa[class_activity], mapa[explication])

        await conn.execute("""
            UPDATE inscripciones SET ya_voto = true
            WHERE id_estudiante = (SELECT id FROM estudiantes WHERE email = $1)
            AND id_asignacion IN (
                SELECT a.id FROM asignaciones a
                JOIN maestros m ON m.id = a.id_profesor
                WHERE m.nombre = $2
            )
        """, email, profesor)