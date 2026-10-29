# =============================================================================
# repositorio.py — Acceso a datos y operaciones CRUD con PostgreSQL
# =============================================================================
# Este archivo contiene todas las consultas directas a la base de datos.
# Cada función recibe una conexión asyncpg (ConnectionDep) y opera de forma asíncrona.
# Depende de: app/seguridad.py → hash_password() para encriptar contraseñas,
#             verify_password() para validar credenciales en el login.
# Es usada por: app/vistas.py → los endpoints HTTP llaman aquí para persistir/leer datos.
# =============================================================================

from logging import exception

from app.seguridad import hash_password, verify_password


# ── Autenticación ──────────────────────────────────────────────────────────────
# Funciones que verifican credenciales de estudiantes y administradores.
# Comparan la contraseña en texto plano contra el hash almacenado usando Argon2id.

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

# ── Validación de unicidad ─────────────────────────────────────────────────────
# Verifica si un email ya existe en la base de datos para evitar duplicados.

async def existe_email(conn, email: str) -> bool:
    row = await conn.fetchrow("SELECT 1 FROM estudiantes WHERE email = $1", email)
    return row is not None
async def existe_email_admin(conn, email: str) -> bool:
    row = await conn.fetchrow("SELECT 1 FROM administradores WHERE email = $1", email)
    return row is not None

# ── Registro de estudiantes ───────────────────────────────────────────────────
# Crea un nuevo estudiante en la tabla correspondiente.
# La contraseña se hashea con Argon2id antes de almacenarse.
# Usa una transacción para asegurar atomicidad en la inserción.

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

# ── Registro de profesores ────────────────────────────────────────────────────
# Crea un nuevo maestro y lo inscribe automáticamente en todas las asignaciones
# correspondientes a su especialidad durante periodos con estado 'abierto'.
# Usa transacción para asegurar que el maestro y sus inscripciones se creen juntos.

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

# ── Consulta de profesores asignados ──────────────────────────────────────────
# Devuelve la lista de profesores que un estudiante puede evaluar.
# Filtra solo los profesores cuyas asignaciones aún no han sido votadas por el estudiante.

async def select_profesor(conn, email: str) -> list[dict]:
    rows = await conn.fetch("""
SELECT DISTINCT maestros.nombre, m.nombre_materia, asignaciones.id_materia
FROM asignaciones
JOIN maestros ON maestros.id = asignaciones.id_profesor
JOIN estudiantes ON estudiantes.id_grado = asignaciones.id_grado
JOIN materias m ON m.id = asignaciones.id_materia
LEFT JOIN inscripciones
    ON inscripciones.id_asignacion = asignaciones.id
    AND inscripciones.id_estudiante = estudiantes.id
WHERE estudiantes.email = $1
    AND (inscripciones.ya_voto IS NULL OR inscripciones.ya_voto = false)
    """, email)
    return [dict(row) for row in rows] if rows else []

# ── Consulta de nombre de estudiante ──────────────────────────────────────────
# Obtiene el nombre del estudiante a partir de su email.
# Se usa para mostrar el nombre del usuario en las vistas.

async def nombre_estudiante(conn, email: str) -> dict | None:
    row = await conn.fetchrow(
        "SELECT nombre FROM estudiantes WHERE email = $1",
        email
    )
    return dict(row) if row else None


# ── Registro de calificaciones ────────────────────────────────────────────────
# Permite a un estudiante enviar su evaluación de un profesor.
# Convierte las etiquetas ("Malo", "Regular", "Bien", "Excelente") a valores numéricos 1-4.
# Marca la inscripción como "ya_voto = true" para impedir votaciones duplicadas.
# Lanza ValueError si no encuentra asignación activa (profesor + grado + periodo abierto).

async def registrar_calificacion(
    conn, email: str, profesor: str,
    explication: int, actitudinal: int, class_activity: int, id_materia: int
) -> None:
    
    profesor = profesor.strip()

    async with conn.transaction():
        asignaciones = await conn.fetch("""
            SELECT a.id
            FROM asignaciones a
            JOIN maestros m ON m.id = a.id_profesor
            JOIN estudiantes e ON e.id_grado = a.id_grado
            JOIN periodos p ON p.id = a.id_periodo
            JOIN inscripciones i ON i.id_asignacion = a.id AND i.id_estudiante = e.id
            WHERE e.email = $1 AND m.nombre = $2 AND a.id_materia = $3
                AND p.estado = 'abierto' AND i.ya_voto = false
        """, email, profesor, id_materia)

        if not asignaciones:
            raise ValueError("No se encontró la asignación para esta evaluación")

        for a in asignaciones:
            await conn.execute("""
                INSERT INTO evaluaciones (id_asignacion, actitudinal, actividades, metodologia)
                VALUES ($1, $2, $3, $4)
            """, a["id"], actitudinal,class_activity, explication)

        await conn.execute("""
            UPDATE inscripciones SET ya_voto = true
            WHERE id_estudiante = (SELECT id FROM estudiantes WHERE email = $1)
            AND id_asignacion IN (
                SELECT a.id FROM asignaciones a
                JOIN maestros m ON m.id = a.id_profesor
                WHERE m.nombre = $2
                AND a.id_materia = $3
            )
        """, email, profesor, id_materia)

# ── Estadísticas admin: mejor y peor maestro ──────────────────────────────────
# Devuelven los 5 profesores con las calificaciones más altas y más bajas.
# El promedio se calcula como el promedio de los 3 criterios: actitudinal,
# actividades y metodología (escala 1-4 por criterio).
# Se agrupa por maestro (GROUP BY m.id) para evitar duplicados por múltiples asignaciones.

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

# ── Estadísticas admin: promedio general por grado (6° a 11°) ─────────────────
# Cada función calcula el promedio acumulado de todas las evaluaciones de un grado.
# La escala de calificación es: {"Malo": 1, "Regular": 2, "Bien": 3, "Excelente": 4}.
# El promedio se calcula como (actitudinal + actividades + metodología) / 3 por cada evaluación,
# y luego se promedia entre todas las evaluaciones del grado.
# Devuelven el promedio como string (formato "X.XX") o None si no hay datos.

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

# ── Estadísticas admin: conteos generales ──────────────────────────────────────
# Devuelven el número total de registros en cada tabla principal.
# Se usan en el dashboard admin para mostrar métricas de alto nivel.
# n_inscripciones_admin cuenta solo las inscripciones ya votadas (ya_voto = TRUE).

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


# ── Estadísticas admin: conteos de estudiantes por grado ───────────────────────
# Cada función cuenta los estudiantes matriculados en un grado específico.
# id_grado es un número: 1 = 6°, 2 = 7°, 3 = 8°, 4 = 9°, 5 = 10°, 6 = 11°.
# Se usan en estadisticas_admin para desglosar el total por grado.

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

# ── Estadísticas admin: consolidada ────────────────────────────────────────────
# Compila todas las métricas del dashboard admin en un solo diccionario.
# Llama a todas las funciones anteriores en un solo punto para optimizar el acceso.
# Las claves del diccionario se usan directamente en las plantillas Jinja2:
#   nde = número de estudiantes, ndm = número de maestros, ndi = inscripciones, ndg = grados
#   mma = mejores maestros, pma = peores maestros
#   p6 a p11 = promedios por grado, n_e_1 a n_e_6 = estudiantes por grado

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

# ── Consultas de detalle: detalle_por_grado ────────────────────────────────────
# Consulta compleja con CTEs (Common Table Expressions) que devuelve un resumen por grado.
# Muestra: número de profesores, estudiantes, promedio general, mejor profesor y estado del periodo.
# Se usa en la vista de detalle del dashboard admin para mostrar información por grado.
#
# CTEs utilizados:
#   estudiantes_por_grado:   Cuenta estudiantes matriculados por grado
#   promedios_asignacion:    Calcula promedio por cada evaluación (3 criterios)
#   promedio_por_profesor:   Agrupa promedios por profesor dentro de su grado
#   mejor_profesor_grado:    Usa ROW_NUMBER para seleccionar al profesor con mayor promedio
#   promedio_general_grado:  Promedio acumulado de todas las evaluaciones del grado
#   estado_periodo:          Estado del periodo (abierto/cerrado) por grado (más reciente)

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

# ── Consultas de detalle: listado de estudiantes ───────────────────────────────
# Devuelve la lista completa de estudiantes con su nombre, email y grado.
# Se usa para mostrar la tabla de estudiantes en la vista admin de gestión.
# JOIN con grados para obtener el nombre del grado (ej: "6°", "7°") en lugar del ID.

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

# ── Actualización de estudiante ───────────────────────────────────────────────
# Modifica los datos de un estudiante existente: nombre, email y grado.
# Nota: el nombre de la función tiene un typo ("actualizarectudiante" en vez de "actualizarestudiante").
# Usa RETURNING * para devolver el registro actualizado.

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

# ── Consulta de todos los profesores (panel admin) ────────────────────────────
# Devuelve todos los profesores con su grado asignado y promedio de evaluación.
# Se usa en el panel de administración para gestionar la lista de profesores.
# Retorna lista de dicts: {id, nombre, grado_asignado, promedio_eval, estado}

async def obtener_todos_los_profesores(conn) -> list[dict]:
    rows = await conn.fetch("""
SELECT
    m.id,
    m.nombre,
    COALESCE(
        STRING_AGG(DISTINCT g.nombre_grado, ', ' ORDER BY g.nombre_grado),
        'Sin grado asignado'
    ) AS grados_asignados,
    COALESCE(
        ROUND(
            (
                AVG(
                    (e.actitudinal + e.actividades + e.metodologia) / 3.0
                )
            )::numeric,
            1
        ),
        0.0
    ) AS promedio_eval
FROM maestros m
LEFT JOIN asignaciones a
    ON a.id_profesor = m.id
LEFT JOIN grados g
    ON a.id_grado = g.id_grado
LEFT JOIN evaluaciones e
    ON e.id_asignacion = a.id
GROUP BY
    m.id,
    m.nombre
ORDER BY
    m.nombre
    """)
    result = []
    for row in rows:
        promedio = float(row["promedio_eval"])
        estado = "Activo" if promedio >= 4.0 else "Alerta"
        result.append({
            "id": row["id"],
            "nombre": row["nombre"],
            "grados_asignados": row["grados_asignados"] or "Sin asignar",
            "promedio_eval": promedio,
            "estado": estado,
        })
    return result


# ── Consultas de detalle: estudiante individual ───────────────────────────────
# Devuelve los datos de un único estudiante filtrado por su ID.
# Se usa para mostrar el formulario de edición con los datos actuales.

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

# ── Eliminación de estudiante ────────────────────────────────────────────────
# Elimina un estudiante y todas sus inscripciones relacionadas.
# Primero borra las inscripciones (para respetar restricciones de clave foránea),
# luego borra el estudiante de la tabla correspondiente.
# Retorna True si se eliminó exactamente 1 estudiante (verifica el resultado del DELETE).

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


# ── Eliminación de grado ────────────────────────────────────────────────────
# Elimina un grado SOLO si no tiene estudiantes ni asignaciones asociadas
# (operación segura: no borra en cascada nada de lo que cuelga del grado).
# Retorna True si se eliminó exactamente 1 grado.

async def eliminar_grado(conn, id_grado: int) -> bool:
    fila = await conn.fetchrow(
        """
        SELECT
            (SELECT COUNT(*) FROM estudiantes  WHERE id_grado = $1) AS n_estudiantes,
            (SELECT COUNT(*) FROM asignaciones WHERE id_grado = $1) AS n_asignaciones
        """,
        id_grado,
    )
    if fila["n_estudiantes"] > 0 or fila["n_asignaciones"] > 0:
        return False
    result = await conn.execute(
        "DELETE FROM grados WHERE id_grado = $1",
        id_grado,
    )
    return result == "DELETE 1"

async def eliminar_profesor(conn, id_profesor: int) -> bool:
    result = await conn.execute(
        "DELETE FROM maestros WHERE id = $1",
        id_profesor,
    )
    return result == "DELETE 1"


# ── Listado de grados (panel admin) ─────────────────────────────────────────
# Devuelve TODOS los grados existentes con su conteo real de estudiantes y
# de profesores asignados (vía asignaciones). Se usa en la vista de gestión
# de grados para renderizar una tarjeta por grado con datos de la BD.
# Retorna lista de dicts: {id_grado, nombre_grado, n_estudiantes, n_profesores}

async def listar_grados(conn) -> list[dict]:
    rows = await conn.fetch("""
        SELECT
            g.id_grado,
            g.nombre_grado,
            (SELECT COUNT(*) FROM estudiantes e
            WHERE e.id_grado = g.id_grado) AS n_estudiantes,
            (SELECT COUNT(DISTINCT a.id_profesor) FROM asignaciones a
            WHERE a.id_grado = g.id_grado) AS n_profesores
        FROM grados g
        ORDER BY g.id_grado;
    """)
    return [dict(row) for row in rows] if rows else []



# ── Catálogos para nuevo profesor ─────────────────────────────────────────────
# Devuelven las listas desplegables que el formulario de "Nuevo profesor" necesita:
# materias (id, nombre_materia), periodos (id, nombre, estado).
# Para los grados se reutiliza listar_grados() de arriba ({id_grado, nombre_grado, ...}).

async def listar_materias(conn) -> list[dict]:
    rows = await conn.fetch("""
        SELECT id, nombre_materia
        FROM materias
        ORDER BY nombre_materia;
    """)
    return [dict(row) for row in rows] if rows else []

async def listar_periodos(conn) -> list[dict]:
    rows = await conn.fetch("""
        SELECT id, nombre, estado
        FROM periodos
        ORDER BY id DESC;
    """)
    return [dict(row) for row in rows] if rows else []


# ── Nuevo profesor (alta completa) ────────────────────────────────────────────
# Crea el maestro, una asignación por cada materia × grado seleccionado
# (producto cruzado, todas con el mismo periodo) y matricula automáticamente
# a los estudiantes existentes de cada grado en su nueva asignación.
# Lanza ValueError si materias o grados vienen vacíos. Devuelve el id del maestro.

async def guardar_maestro(conn, nombre: str, materias: list[int], grados: list[int], id_periodo: int) -> int:
    if not materias or not grados:
        raise ValueError("Debe indicar al menos una materia y un grado")

    async with conn.transaction():
        id_profesor = await conn.fetchval(
            """
            INSERT INTO maestros (nombre)
            VALUES ($1)
            RETURNING id
            """,
            nombre.strip()
        )

        for id_materia in materias:
            for id_grado in grados:
                id_asignacion = await conn.fetchval(
                    """
                    INSERT INTO asignaciones (id_profesor, id_materia, id_grado, id_periodo)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id
                    """,
                    id_profesor, id_materia, id_grado, id_periodo
                )

                await conn.execute(
                    """
                    INSERT INTO inscripciones (id_estudiante, id_asignacion)
                    SELECT id, $2 FROM estudiantes WHERE id_grado = $1
                    ON CONFLICT (id_estudiante, id_asignacion) DO NOTHING
                    """,
                    id_grado, id_asignacion
                )

    return id_profesor


# ── Profesor individual (edición inline, panel admin) ────────────────────────
# Devuelve los datos de UN profesor para el formulario de edición inline (htmx).
# Misma consulta/agregados que obtener_todos_los_profesores(), con WHERE m.id = $1.
# Se mantiene GROUP BY m.id, m.nombre: sin él, un ID inexistente devolvería una
# fila de agregados NULL en vez de ninguna fila (rompería el retorno None).
# Retorna dict: {id, nombre, grados_asignados, promedio_eval, estado} o None.

async def detalle_por_profesor(conn, id_profesor: int) -> dict | None:
    row = await conn.fetchrow("""
        SELECT
            m.id,
            m.nombre,
            COALESCE(
                STRING_AGG(DISTINCT g.nombre_grado, ', ' ORDER BY g.nombre_grado),
                'Sin grado asignado'
            ) AS grados_asignados,
            COALESCE(
                ROUND(
                    (
                        AVG(
                            (e.actitudinal + e.actividades + e.metodologia) / 3.0
                        )
                    )::numeric,
                    1
                ),
                0.0
            ) AS promedio_eval
        FROM maestros m
        LEFT JOIN asignaciones a
            ON a.id_profesor = m.id
        LEFT JOIN grados g
            ON a.id_grado = g.id_grado
        LEFT JOIN evaluaciones e
            ON e.id_asignacion = a.id
        WHERE m.id = $1
        GROUP BY
            m.id,
            m.nombre
        """, id_profesor)
    if row is None:
        return None
    promedio = float(row["promedio_eval"])
    return {
        "id": row["id"],
        "nombre": row["nombre"],
        "grados_asignados": row["grados_asignados"] or "Sin asignar",
        "promedio_eval": promedio,
        "estado": "Activo" if promedio >= 4.0 else "Alerta",
    }


# ── Actualización de profesor ────────────────────────────────────────────────
# Modifica el nombre de un profesor existente (único campo editable inline).
# Usa RETURNING * para devolver el registro actualizado (patrón actualizarectudiante).

async def actualizar_profesor(conn, id_profesor: int, nombre: str) -> dict | None:
    row = await conn.fetchrow(
        """
        UPDATE maestros
        SET nombre = $2
        WHERE id = $1
        RETURNING *
        """,
        id_profesor, nombre
    )
    return dict(row) if row else None
