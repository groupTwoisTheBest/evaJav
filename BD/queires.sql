-- ============================================================
-- evaJav — Plataforma de evaluación docente anónima
-- queries.sql — Proyecto Final CS50 SQL
-- Consultas típicas que ejecutaría la aplicación FastAPI.
-- ============================================================


-- ------------------------------------------------------------
-- 1. AUTENTICACIÓN
-- ------------------------------------------------------------

-- Buscar un estudiante por email para verificar su contraseña
-- (el hash se compara en la aplicación, no en SQL).
SELECT id, nombre, contrasenna, id_grado
FROM estudiantes
WHERE email = '$1';

-- Registrar un nuevo estudiante.
INSERT INTO estudiantes (nombre, contrasenna, email, id_grado)
VALUES ('$1', '$2', '$3', $4);


-- ------------------------------------------------------------
-- 2. CONSULTAS PARA EL ESTUDIANTE (flujo de votación)
-- ------------------------------------------------------------

-- Listar las asignaciones (profesor + materia) pendientes de
-- evaluar por un estudiante, solo si el periodo está abierto
-- y el estudiante todavía no ha votado por esa asignación.
SELECT maestros.nombre FROM inscripciones 
JOIN asignaciones ON inscripciones.id_asignacion = asignaciones.id
JOIN estudiantes ON inscripciones.id_estudiante = estudiantes.id
JOIN maestros ON asignaciones.id_profesor = maestros.id
WHERE inscripciones.ya_voto = false;

-- Registrar una evaluación anónima. Nótese que esta sentencia
-- nunca recibe el id del estudiante: solo el id de la
-- asignación que está siendo calificada.
INSERT INTO evaluaciones (id_asignacion, actitudinal, actividades, metodologia)
VALUES ($1, $2, $3, $4);

-- Marcar que el estudiante ya votó por esa asignación, para
-- que no pueda volver a hacerlo. Esta actualización ocurre en
-- la misma transacción que el INSERT anterior, pero al no
-- compartir columnas, no revela qué evaluación corresponde a
-- qué estudiante.
UPDATE inscripciones
SET ya_voto = true
WHERE id_estudiante = $1
  AND id_asignacion = $2;

-- Matricular a un estudiante en una asignación (lo haría un
-- administrador al cargar la lista de clases del periodo).
INSERT INTO inscripciones (id_estudiante, id_asignacion)
VALUES ($1, $2);


-- ------------------------------------------------------------
-- 3. CONSULTAS PARA EL ADMINISTRADOR (panel de resultados)
-- ------------------------------------------------------------

-- Resultados promedio de todas las asignaciones del periodo
-- actual, usando la vista definida en schema.sql.
SELECT *
FROM resultados_por_asignacion
WHERE periodo = '$1'
ORDER BY promedio_metodologia DESC;

-- Detalle de resultados de un profesor específico a través de
-- todos los periodos en los que ha sido evaluado.
SELECT
    p.nombre                     AS periodo,
    mat.nombre_materia           AS materia,
    COUNT(e.id)                  AS total_evaluaciones,
    ROUND(AVG(e.actitudinal), 2) AS promedio_actitudinal,
    ROUND(AVG(e.actividades), 2) AS promedio_actividades,
    ROUND(AVG(e.metodologia), 2) AS promedio_metodologia
FROM asignaciones a
JOIN maestros  m   ON m.id = a.id_profesor
JOIN materias  mat ON mat.id = a.id_materia
JOIN periodos  p   ON p.id = a.id_periodo
JOIN evaluaciones e ON e.id_asignacion = a.id
WHERE m.id = $1
GROUP BY p.nombre, mat.nombre_materia
ORDER BY p.nombre;

-- Porcentaje de participación por asignación: inscritos vs.
-- estudiantes que ya votaron. Útil para que el administrador
-- decida cuándo cerrar el periodo.
SELECT
    a.id AS id_asignacion,
    m.nombre AS profesor,
    mat.nombre_materia AS materia,
    COUNT(i.id) AS total_inscritos,
    COUNT(i.id) FILTER (WHERE i.ya_voto) AS total_votaron,
    ROUND(
        100.0 * COUNT(i.id) FILTER (WHERE i.ya_voto) / NULLIF(COUNT(i.id), 0),
        1
    ) AS porcentaje_participacion
FROM asignaciones a
JOIN maestros m   ON m.id = a.id_profesor
JOIN materias mat ON mat.id = a.id_materia
LEFT JOIN inscripciones i ON i.id_asignacion = a.id
GROUP BY a.id, m.nombre, mat.nombre_materia
ORDER BY porcentaje_participacion ASC;

-- Abrir el periodo de votación actual.
UPDATE periodos
SET estado = '$1'
WHERE nombre = '$2';

-- Cerrar el periodo de votación actual (por ejemplo, al
-- vencerse la fecha_fin).
UPDATE periodos
SET estado = '$1'
WHERE nombre = '$2';

-- Crear una nueva asignación (asignar un profesor a una
-- materia y grado dentro de un periodo).
INSERT INTO asignaciones (id_profesor, id_materia, id_periodo, id_grado)
VALUES ($1, $2, $3, $4);

--dasboar admin 

SELECT COUNT(*) FROM estudiantes

SELECT COUNT(*) FROM maestros

SELECT COUNT(*) FROM grados

SELECT COUNT(*) FROM inscripciones WHERE ya_voto = TRUE


--graficas

--top 5 maestros con mejores calificacion promedio
SELECT m.nombre AS maestro, ROUND(AVG((e.actitudinal + e.actividades + e.metodologia) / 3.0), 2) AS calificacion_promedio
    FROM maestros AS m
    JOIN asignaciones AS a ON m.id = a.id_profesor
    JOIN evaluaciones AS e ON a.id = e.id_asignacion
    GROUP BY m.id
    ORDER BY calificacion_promedio DESC
    LIMIT 5;

--top 5 maestros con peores calificaciones promedio
SELECT m.nombre AS maestro, ROUND(AVG((e.actitudinal + e.actividades + e.metodologia) / 3.0), 2) AS calificacion_promedio
    FROM maestros AS m
    JOIN asignaciones AS a ON m.id = a.id_profesor
    JOIN evaluaciones AS e ON a.id = e.id_asignacion
    GROUP BY m.id
    ORDER BY calificacion_promedio ASC
    LIMIT 5;

--tabla de barras
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

--grafica de pastel
SELECT COUNT(*) FROM estudiantes where id_grado = 1
SELECT COUNT(*) FROM estudiantes where id_grado = 2
SELECT COUNT(*) FROM estudiantes where id_grado = 3
SELECT COUNT(*) FROM estudiantes where id_grado = 4
SELECT COUNT(*) FROM estudiantes where id_grado = 5
SELECT COUNT(*) FROM estudiantes where id_grado = 6

--centro de control
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
    epg.total_estudiantes, -- no creo que esto haga algo, pero lo dejo por si acaso
    pgg.promedio_general, 
    mpg.nombre_profesor, 
    ep.estado
ORDER BY g.id_grado ASC;

SELECT 
    e.id AS id_estudiante,
    e.nombre AS nombre_estudiante,
    e.email,
    g.nombre_grado AS grado
FROM estudiantes e
JOIN grados g ON e.id_grado = g.id_grado;



-- ------------------------------------------------------------
-- 4. MANTENIMIENTO Y CORRECCIÓN DE DATOS
-- ------------------------------------------------------------

-- Corregir el nombre de un profesor.
UPDATE maestros
SET nombre = '$1'
WHERE id = $2;

-- Eliminar una asignación creada por error, siempre que no
-- tenga inscripciones ni evaluaciones asociadas (las FK sin
-- ON DELETE CASCADE lo impiden si ya tiene datos).
DELETE FROM asignaciones
WHERE id = $1;

-- Retirar a un estudiante de una asignación en la que fue
-- inscrito por error, antes de que haya votado.
DELETE FROM inscripciones
WHERE id_estudiante = $1
  AND id_asignacion = $2
  AND ya_voto = $3;