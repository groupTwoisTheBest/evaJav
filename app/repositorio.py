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

async def registrar_maestro(conn, nombre: str, email: str, contrasenna: str, especialidad: str) -> None:
    async with conn.transaction():
        maestro_id = await conn.fetchval(
            """
            INSERT INTO maestros (nombre, contrasenna, email, especialidad)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            """,
            nombre, hash_password(contrasenna), email, especialidad
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
            maestro_id, especialidad
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

async def mejor_maestro_admin(conn) -> dict | None:
    rows = await conn.fetch(
        """
        SELECT m.nombre AS maestro, ROUND(AVG((e.actitudinal + e.actividades + e.metodologia) / 3.0), 2) AS calificacion_promedio
        FROM maestros AS m
        JOIN asignaciones AS a ON m.id = a.id_profesor
        JOIN evaluaciones AS e ON a.id = e.id_asignacion
        GROUP BY m.id
        ORDER BY calificacion_promedio DESC
        LIMIT 5;
        """
    )
    return [dict(row) for row in rows] if rows else None

async def peor_maestro_admin(conn) -> list | None:
    rows = await conn.fetch(
        """
        SELECT m.nombre AS maestro, ROUND(AVG((e.actitudinal + e.actividades + e.metodologia) / 3.0), 2) AS calificacion_promedio
        FROM maestros AS m
        JOIN asignaciones AS a ON m.id = a.id_profesor
        JOIN evaluaciones AS e ON a.id = e.id_asignacion
        GROUP BY m.id
        ORDER BY calificacion_promedio ASC
        LIMIT 5;
        """
    )
    return [dict(row) for row in rows] if rows else None

async def promedio_11_admin(conn) -> str | None:
    row = await conn.fetchrow(
        """
        SELECT 
    ROUND(AVG(promedio_general), 2) AS promedio_total_grado_once
FROM (
    SELECT 
        (e.actitudinal + e.actividades + e.metodologia) / 3.0 AS promedio_general
    FROM evaluaciones e
    JOIN asignaciones a ON e.id_asignacion = a.id
    JOIN grados g ON a.id_grado = g.id_grado
    WHERE g.nombre_grado = '11'
) AS subconsulta;
        """
    )
    return str(row[0]) if row else None

async def promedio_10_admin(conn) -> str | None:
    row = await conn.fetchrow(
        """
        SELECT 
    ROUND(AVG(promedio_general), 2) AS promedio_total_grado_once
FROM (
    SELECT 
        (e.actitudinal + e.actividades + e.metodologia) / 3.0 AS promedio_general
    FROM evaluaciones e
    JOIN asignaciones a ON e.id_asignacion = a.id
    JOIN grados g ON a.id_grado = g.id_grado
    WHERE g.nombre_grado = '10'
) AS subconsulta;
        """
    )
    return str(row[0]) if row else None

async def promedio_9_admin(conn) -> str | None:
    row = await conn.fetchrow(
        """
        SELECT 
    ROUND(AVG(promedio_general), 2) AS promedio_total_grado_once
FROM (
    SELECT 
        (e.actitudinal + e.actividades + e.metodologia) / 3.0 AS promedio_general
    FROM evaluaciones e
    JOIN asignaciones a ON e.id_asignacion = a.id
    JOIN grados g ON a.id_grado = g.id_grado
    WHERE g.nombre_grado = '9'
) AS subconsulta;
        """
    )
    return str(row[0]) if row else None

async def promedio_8_admin(conn) -> str | None:
    row = await conn.fetchrow(
        """
        SELECT 
    ROUND(AVG(promedio_general), 2) AS promedio_total_grado_once
FROM (
    SELECT 
        (e.actitudinal + e.actividades + e.metodologia) / 3.0 AS promedio_general
    FROM evaluaciones e
    JOIN asignaciones a ON e.id_asignacion = a.id
    JOIN grados g ON a.id_grado = g.id_grado
    WHERE g.nombre_grado = '8'
) AS subconsulta;
        """
    )
    return str(row[0]) if row else None

async def promedio_7_admin(conn) -> str | None:
    row = await conn.fetchrow(
        """
        SELECT 
    ROUND(AVG(promedio_general), 2) AS promedio_total_grado_once
FROM (
    SELECT 
        (e.actitudinal + e.actividades + e.metodologia) / 3.0 AS promedio_general
    FROM evaluaciones e
    JOIN asignaciones a ON e.id_asignacion = a.id
    JOIN grados g ON a.id_grado = g.id_grado
    WHERE g.nombre_grado = '7'
) AS subconsulta;
        """
    )
    return str(row[0]) if row else None

async def promedio_6_admin(conn) -> str | None:
    row = await conn.fetchrow(
        """
        SELECT 
    ROUND(AVG(promedio_general), 2) AS promedio_total_grado_once
FROM (
    SELECT 
        (e.actitudinal + e.actividades + e.metodologia) / 3.0 AS promedio_general
    FROM evaluaciones e
    JOIN asignaciones a ON e.id_asignacion = a.id
    JOIN grados g ON a.id_grado = g.id_grado
    WHERE g.nombre_grado = '6'
) AS subconsulta;
        """
    )
    return str(row[0]) if row else None

async def n_estudiantes_admin (conn) -> int | None:
    row = await conn.fetchrow(
        "SELECT COUNT(*) FROM estudiantes"
    )
    return int(row[0]) if row else None

async def n_maestros_admin (conn) -> int | None:
    row = await conn.fetchrow(
        "SELECT COUNT(*) FROM maestros"
    )
    return int(row[0]) if row else None

async def n_inscripciones_admin (conn) -> int | None:
    row = await conn.fetchrow(
        "SELECT COUNT(*) FROM inscripciones WHERE ya_voto = TRUE"
    )
    return int(row[0]) if row else None

async def n_grados_admin (conn) -> int | None:
    row = await conn.fetchrow(
        "SELECT COUNT(*) FROM grados"
    )
    return int(row[0]) if row else None


async def n_e_admin_1 (conn) -> int | None:
    row = await conn.fetchrow(
        "SELECT COUNT(*) FROM estudiantes where id_grado = 1"
    )
    return int(row[0]) if row else None

async def n_e_admin_2 (conn) -> int | None:
    row = await conn.fetchrow(
        "SELECT COUNT(*) FROM estudiantes where id_grado = 2"
    )
    return int(row[0]) if row else None

async def n_e_admin_3 (conn) -> int | None:
    row = await conn.fetchrow(
        "SELECT COUNT(*) FROM estudiantes where id_grado = 3"
    )
    return int(row[0]) if row else None

async def n_e_admin_4 (conn) -> int | None:
    row = await conn.fetchrow(
        "SELECT COUNT(*) FROM estudiantes where id_grado = 4"
    )
    return int(row[0]) if row else None

async def n_e_admin_5 (conn) -> int | None:
    row = await conn.fetchrow(
        "SELECT COUNT(*) FROM estudiantes where id_grado = 5"
    )
    return int(row[0]) if row else None

async def n_e_admin_6 (conn) -> int | None:
    row = await conn.fetchrow(
        "SELECT COUNT(*) FROM estudiantes where id_grado = 6"
    )
    return int(row[0]) if row else None

async def estadisticas_admin(conn):
    return {
    "nde": await n_estudiantes_admin(conn),     
    "ndm": await n_maestros_admin(conn),
    "ndi": await n_inscripciones_admin(conn),
    "ndg": await n_grados_admin(conn),
    "mma": await mejor_maestro_admin(conn),
    "pma": await peor_maestro_admin(conn),
    "p11": await promedio_11_admin(conn),
    "p10": await promedio_10_admin(conn),
    "p9": await promedio_9_admin(conn),
    "p8": await promedio_8_admin(conn),
    "p7": await promedio_7_admin(conn),
    "p6": await promedio_6_admin(conn),
    "n_e_1": await n_e_admin_1(conn),
    "n_e_2": await n_e_admin_2(conn),
    "n_e_3": await n_e_admin_3(conn),
    "n_e_4": await n_e_admin_4(conn),
    "n_e_5": await n_e_admin_5(conn),
    "n_e_6": await n_e_admin_6(conn)
    }

async def detalle_por_grado (conn) -> dict | None:
    rows = await conn.fetch("""
        WITH estudiantes_por_grado AS (
    -- Cuenta los estudiantes matriculados en cada grado
    SELECT 
        id_grado, 
        COUNT(id) AS total_estudiantes
    FROM estudiantes
    GROUP BY id_grado
),
promedios_asignacion AS (
    -- Obtiene el promedio de cada asignación (promedio de los 3 criterios)
    SELECT 
        a.id AS id_asignacion,
        a.id_grado,
        a.id_profesor,
        m.nombre AS nombre_profesor,
        ((ev.actitudinal + ev.actividades + ev.metodologia) / 3.0) AS promedio_asignacion
    FROM asignaciones a
    JOIN maestros m ON m.id = a.id_profesor
    LEFT JOIN evaluaciones ev ON ev.id_asignacion = a.id
),
promedio_por_profesor AS (
    -- Agrupa el promedio general por cada profesor dentro de su grado
    SELECT 
        id_grado,
        id_profesor,
        nombre_profesor,
        AVG(promedio_asignacion) AS promedio_profesor
    FROM promedios_asignacion
    GROUP BY id_grado, id_profesor, nombre_profesor
),
mejor_profesor_grado AS (
    -- Selecciona al profesor con la calificación más alta por grado
    SELECT 
        id_grado,
        nombre_profesor,
        ROW_NUMBER() OVER (PARTITION BY id_grado ORDER BY promedio_profesor DESC NULLS LAST) AS rn
    FROM promedio_por_profesor
),
promedio_general_grado AS (
    -- Calcula el promedio general acumulado de todas las evaluaciones del grado
    SELECT 
        id_grado,
        AVG(promedio_asignacion) AS promedio_general
    FROM promedios_asignacion
    GROUP BY id_grado
),
estado_periodo AS (
    -- Obtiene el estado del periodo asociado al grado (si hay varios, toma el más reciente)
    SELECT DISTINCT ON (a.id_grado)
        a.id_grado,
        p.estado
    FROM asignaciones a
    JOIN periodos p ON p.id = a.id_periodo
    ORDER BY a.id_grado, p.id DESC
)
SELECT 
    g.nombre_grado AS Grado,
    COUNT(DISTINCT a.id_profesor) AS Numero_de_Profesores,
    COALESCE(epg.total_estudiantes, 0) AS Estudiantes,
    ROUND(COALESCE(pgg.promedio_general, 0), 2) AS Promedio_General,
    COALESCE(mpg.nombre_profesor, 'Sin evaluaciones') AS Mejor_Profesor,
    COALESCE(ep.estado, 'Sin periodo') AS Estado
FROM grados g
LEFT JOIN estudiantes_por_grado epg ON epg.id_grado = g.id_grado
LEFT JOIN asignaciones a ON a.id_grado = g.id_grado
LEFT JOIN promedio_general_grado pgg ON pgg.id_grado = g.id_grado
LEFT JOIN mejor_profesor_grado mpg ON mpg.id_grado = g.id_grado AND mpg.rn = 1
LEFT JOIN estado_periodo ep ON ep.id_grado = g.id_grado
GROUP BY 
    g.id_grado, 
    g.nombre_grado, 
    epg.total_estudiantes, 
    pgg.promedio_general, 
    mpg.nombre_profesor, 
    ep.estado
ORDER BY g.id_grado ASC;
"""
    )
    return [dict(row) for row in rows] if rows else None     

async def detalle_estudiantes(conn) -> list[dict]:
    rows = await conn.fetch("""
        SELECT 
            e.id AS id_estudiante,
            e.nombre AS nombre_estudiante,
            e.email,
            g.nombre_grado AS grado
        FROM estudiantes e
        JOIN grados g ON e.id_grado = g.id_grado;
    """)
    return [dict(row) for row in rows] if rows else None   

async def actualizarectudiante(conn, id_estudiante: int, nombre: str, email: str, grado: int) -> dict | None:
    row =await conn.fetchrow(
       """
       UPDATE estudiantes
       SET nombre = $1, email = $2, id_grado = $3
       WHERE id = $4
       RETURNING *
       """,
       nombre, email, grado, id_estudiante
        )
    return dict(row) if row else None

async def detalle_por_estudiantes(conn, id_estudiante: int) -> dict | None:
    row = await conn.fetchrow("""
        SELECT 
            e.id AS id_estudiante,
            e.nombre AS nombre_estudiante,
            e.email,
            g.nombre_grado AS grado
        FROM estudiantes e
        JOIN grados g ON e.id_grado = g.id_grado
        WHERE e.id = $1
    """, id_estudiante)
    return dict(row) if row else None   

async def eliminar_estudiante(conn, id_estudiante: int) -> bool:
    result = await conn.execute(
        """
    DELETE FROM inscripciones
    WHERE id_estudiante = $1

        """,id_estudiante
    )
    await conn.execute(
        """
    DELETE FROM estudiantes
    WHERE id = $1
        """,id_estudiante)
    return result == "DELETE 1"