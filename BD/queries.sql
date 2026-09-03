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
WHERE email = 'juan.perez@colegio.edu.co';

-- Registrar un nuevo estudiante.
INSERT INTO estudiantes (nombre, contrasenna, email, id_grado)
VALUES ('Juan Pérez', '$2b$12$hashDeEjemploGeneradoPorBcrypt', 'juan.perez@colegio.edu.co', 3);


-- ------------------------------------------------------------
-- 2. CONSULTAS PARA EL ESTUDIANTE (flujo de votación)
-- ------------------------------------------------------------

-- Listar las asignaciones (profesor + materia) pendientes de
-- evaluar por un estudiante, solo si el periodo está abierto
-- y el estudiante todavía no ha votado por esa asignación.
SELECT
    i.id_asignacion,
    m.nombre           AS profesor,
    mat.nombre_materia AS materia
FROM inscripciones i
JOIN asignaciones a ON a.id = i.id_asignacion
JOIN maestros     m ON m.id = a.id_profesor
JOIN materias   mat ON mat.id = a.id_materia
JOIN periodos     p ON p.id = a.id_periodo
WHERE i.id_estudiante = 1
  AND i.ya_voto = false
  AND p.estado = 'abierto';

-- Registrar una evaluación anónima. Nótese que esta sentencia
-- nunca recibe el id del estudiante: solo el id de la
-- asignación que está siendo calificada.
INSERT INTO evaluaciones (id_asignacion, actitudinal, actividades, metodologia)
VALUES (5, 3, 2, 3);

-- Marcar que el estudiante ya votó por esa asignación, para
-- que no pueda volver a hacerlo. Esta actualización ocurre en
-- la misma transacción que el INSERT anterior, pero al no
-- compartir columnas, no revela qué evaluación corresponde a
-- qué estudiante.
UPDATE inscripciones
SET ya_voto = true
WHERE id_estudiante = 1
  AND id_asignacion = 5;

-- Matricular a un estudiante en una asignación (lo haría un
-- administrador al cargar la lista de clases del periodo).
INSERT INTO inscripciones (id_estudiante, id_asignacion)
VALUES (1, 5);


-- ------------------------------------------------------------
-- 3. CONSULTAS PARA EL ADMINISTRADOR (panel de resultados)
-- ------------------------------------------------------------

-- Resultados promedio de todas las asignaciones del periodo
-- actual, usando la vista definida en schema.sql.
SELECT *
FROM resultados_por_asignacion
WHERE periodo = '2026-2'
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
WHERE m.id = 4
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
SET estado = 'abierto'
WHERE nombre = '2026-2';

-- Cerrar el periodo de votación actual (por ejemplo, al
-- vencerse la fecha_fin).
UPDATE periodos
SET estado = 'cerrado'
WHERE nombre = '2026-2';

-- Crear una nueva asignación (asignar un profesor a una
-- materia y grado dentro de un periodo).
INSERT INTO asignaciones (id_profesor, id_materia, id_periodo, id_grado)
VALUES (4, 2, 3, 5);


-- ------------------------------------------------------------
-- 4. MANTENIMIENTO Y CORRECCIÓN DE DATOS
-- ------------------------------------------------------------

-- Corregir el nombre de un profesor.
UPDATE maestros
SET nombre = 'Carlos Andrés Gómez'
WHERE id = 4;

-- Eliminar una asignación creada por error, siempre que no
-- tenga inscripciones ni evaluaciones asociadas (las FK sin
-- ON DELETE CASCADE lo impiden si ya tiene datos).
DELETE FROM asignaciones
WHERE id = 12;

-- Retirar a un estudiante de una asignación en la que fue
-- inscrito por error, antes de que haya votado.
DELETE FROM inscripciones
WHERE id_estudiante = 7
  AND id_asignacion = 5
  AND ya_voto = false;