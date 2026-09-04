-- ============================================================
-- evaJav — Plataforma de evaluación docente anónima
-- schema.sql — Proyecto Final CS50 SQL
-- Motor: PostgreSQL (hosteado en Neon)
-- ============================================================


-- ------------------------------------------------------------
-- TABLA: grados
-- Catálogo de los grados académicos disponibles en el colegio.
-- ------------------------------------------------------------
CREATE TABLE grados (
    id_grado     integer GENERATED ALWAYS AS IDENTITY,
    nombre_grado varchar(4) NOT NULL,

    CONSTRAINT grados_pkey PRIMARY KEY (id_grado),
    CONSTRAINT grados_nombre_grado_key UNIQUE (nombre_grado)
);


-- ------------------------------------------------------------
-- TABLA: estudiantes
-- Usuarios que inician sesión y emiten evaluaciones.
-- ------------------------------------------------------------
CREATE TABLE estudiantes (
    id          integer GENERATED ALWAYS AS IDENTITY,
    nombre      varchar(60) NOT NULL,

    -- La aplicación siempre debe insertar aquí un hash
    -- (ej. bcrypt vía passlib), nunca la contraseña en texto plano.
    contrasenna text NOT NULL,

    email       text NOT NULL,
    id_grado    integer NOT NULL,

    CONSTRAINT estudiantes_pkey PRIMARY KEY (id),
    CONSTRAINT estudiantes_email_key UNIQUE (email),
    CONSTRAINT estudiantes_id_grado_fkey
        FOREIGN KEY (id_grado) REFERENCES grados (id_grado)
);

CREATE INDEX idx_estudiantes_id_grado ON estudiantes (id_grado);


-- ------------------------------------------------------------
-- TABLA: administradores
-- Usuarios con permisos para consultar resultados agregados
-- y gestionar periodos de votación.
-- ------------------------------------------------------------
CREATE TABLE administradores (
    id          integer GENERATED ALWAYS AS IDENTITY,
    nombre      varchar(60) NOT NULL,

    -- Igual que en estudiantes: siempre hash, nunca texto plano.
    contrasenna text NOT NULL,

    email       text NOT NULL,

    CONSTRAINT administradores_pkey PRIMARY KEY (id),
    CONSTRAINT administradores_email_key UNIQUE (email)
);


-- ------------------------------------------------------------
-- TABLA: maestros
-- Profesores que pueden ser evaluados.
-- ------------------------------------------------------------
CREATE TABLE maestros (
    id     integer GENERATED ALWAYS AS IDENTITY,
    nombre varchar(60) NOT NULL,

    CONSTRAINT maestros_pkey PRIMARY KEY (id)
);


-- ------------------------------------------------------------
-- TABLA: materias
-- Catálogo de asignaturas del colegio.
-- ------------------------------------------------------------
CREATE TABLE materias (
    id             integer GENERATED ALWAYS AS IDENTITY,
    nombre_materia varchar(60) NOT NULL,

    CONSTRAINT materias_pkey PRIMARY KEY (id),
    CONSTRAINT materias_nombre_materia_key UNIQUE (nombre_materia)
);


-- ------------------------------------------------------------
-- TABLA: periodos
-- Ventana de tiempo durante la cual las votaciones están
-- abiertas. Permite que un profesor cambie de materia entre
-- un periodo y otro sin perder el histórico de evaluaciones.
-- ------------------------------------------------------------
CREATE TABLE periodos (
    id            integer GENERATED ALWAYS AS IDENTITY,

    -- Ej: '2026-1', '2026-2'.
    nombre        varchar(20) NOT NULL,

    fecha_inicio  date NOT NULL,
    fecha_fin     date NOT NULL,

    -- Controla si actualmente se pueden registrar evaluaciones
    -- para las asignaciones de este periodo.
    estado        varchar(10) NOT NULL DEFAULT 'cerrado',

    CONSTRAINT periodos_pkey PRIMARY KEY (id),
    CONSTRAINT periodos_nombre_key UNIQUE (nombre),
    CONSTRAINT periodos_estado_check
        CHECK (estado IN ('abierto', 'cerrado')),
    CONSTRAINT periodos_fechas_check
        CHECK (fecha_fin >= fecha_inicio)
);


-- ------------------------------------------------------------
-- TABLA: asignaciones
-- Qué materia dicta cada profesor, a qué grado y en qué
-- periodo. Es la entidad "puente" central del sistema: casi
-- todo lo demás (inscripciones, evaluaciones) cuelga de aquí.
-- ------------------------------------------------------------
CREATE TABLE asignaciones (
    id           integer GENERATED ALWAYS AS IDENTITY,
    id_profesor  integer NOT NULL,
    id_materia   integer NOT NULL,
    id_periodo   integer NOT NULL,

    -- Grado al que va dirigida esta clase. Permite responder
    -- "¿qué profesores le corresponden a un estudiante de
    -- grado X?" con un simple JOIN, sin depender de que ya
    -- existan inscripciones cargadas.
    id_grado     integer NOT NULL,

    CONSTRAINT asignaciones_pkey PRIMARY KEY (id),
    CONSTRAINT asignaciones_id_profesor_fkey
        FOREIGN KEY (id_profesor) REFERENCES maestros (id),
    CONSTRAINT asignaciones_id_materia_fkey
        FOREIGN KEY (id_materia) REFERENCES materias (id),
    CONSTRAINT asignaciones_id_periodo_fkey
        FOREIGN KEY (id_periodo) REFERENCES periodos (id),
    CONSTRAINT asignaciones_id_grado_fkey
        FOREIGN KEY (id_grado) REFERENCES grados (id_grado),

    -- Un mismo profesor no puede tener la misma materia
    -- duplicada para el mismo grado dentro de un mismo periodo
    -- (pero sí puede dictarla a grados distintos: son filas
    -- distintas).
    CONSTRAINT asignaciones_unicas
        UNIQUE (id_profesor, id_materia, id_grado, id_periodo)
);

CREATE INDEX idx_asignaciones_id_profesor ON asignaciones (id_profesor);
CREATE INDEX idx_asignaciones_id_materia  ON asignaciones (id_materia);
CREATE INDEX idx_asignaciones_id_periodo  ON asignaciones (id_periodo);
CREATE INDEX idx_asignaciones_id_grado    ON asignaciones (id_grado);


-- ------------------------------------------------------------
-- TABLA: inscripciones
-- Qué estudiante está matriculado en qué asignación
-- (profesor + materia + grado + periodo).
-- ------------------------------------------------------------
CREATE TABLE inscripciones (
    id             integer GENERATED ALWAYS AS IDENTITY,
    id_estudiante  integer NOT NULL,
    id_asignacion  integer NOT NULL,

    -- Controla que el estudiante solo pueda votar una vez por
    -- esta asignación, SIN necesidad de vincular su identidad
    -- a la evaluación en sí (esa relación no existe en
    -- "evaluaciones", ver más abajo).
    ya_voto        boolean NOT NULL DEFAULT false,

    CONSTRAINT inscripciones_pkey PRIMARY KEY (id),
    CONSTRAINT inscripciones_id_estudiante_fkey
        FOREIGN KEY (id_estudiante) REFERENCES estudiantes (id),
    CONSTRAINT inscripciones_id_asignacion_fkey
        FOREIGN KEY (id_asignacion) REFERENCES asignaciones (id),

    -- Un estudiante no puede inscribirse dos veces a la misma
    -- asignación.
    CONSTRAINT inscripciones_unicas
        UNIQUE (id_estudiante, id_asignacion)
);

CREATE INDEX idx_inscripciones_id_estudiante ON inscripciones (id_estudiante);
CREATE INDEX idx_inscripciones_id_asignacion ON inscripciones (id_asignacion);


-- ------------------------------------------------------------
-- TABLA: evaluaciones
-- Cada evaluación anónima realizada sobre una asignación
-- (profesor + materia + periodo).
--
-- IMPORTANTE: esta tabla NO tiene ninguna columna que
-- referencie a "estudiantes". Esto es intencional: garantiza
-- a nivel de esquema que ninguna consulta pueda vincular una
-- evaluación con la identidad de quien la realizó. El control
-- de "quién ya votó" vive en "inscripciones", no aquí.
--
-- Escala de cada criterio: 1 = Malo, 2 = Bien, 3 = Excelente.
-- La aplicación muestra las etiquetas cualitativas; aquí se
-- guarda el valor numérico para poder calcular promedios (AVG).
-- ------------------------------------------------------------
CREATE TABLE evaluaciones (
    id            integer GENERATED ALWAYS AS IDENTITY,
    id_asignacion integer NOT NULL,

    actitudinal   smallint NOT NULL,
    actividades   smallint NOT NULL,
    metodologia   smallint NOT NULL,

    fecha         timestamp NOT NULL DEFAULT now(),

    CONSTRAINT evaluaciones_pkey PRIMARY KEY (id),
    CONSTRAINT evaluaciones_id_asignacion_fkey
        FOREIGN KEY (id_asignacion) REFERENCES asignaciones (id),

    CONSTRAINT evaluaciones_actitudinal_check
        CHECK (actitudinal BETWEEN 1 AND 3),
    CONSTRAINT evaluaciones_actividades_check
        CHECK (actividades BETWEEN 1 AND 3),
    CONSTRAINT evaluaciones_metodologia_check
        CHECK (metodologia BETWEEN 1 AND 3)
);

CREATE INDEX idx_evaluaciones_id_asignacion ON evaluaciones (id_asignacion);


-- ------------------------------------------------------------
-- VIEW: resultados_por_asignacion
-- Optimización de lectura: la consulta más frecuente del panel
-- de administración es "el promedio de cada criterio por cada
-- asignación, con el nombre del profesor y de la materia ya
-- resueltos". En vez de repetir ese JOIN + AVG + GROUP BY en
-- cada endpoint, se deja resuelto en una vista.
-- ------------------------------------------------------------
CREATE VIEW resultados_por_asignacion AS
SELECT
    a.id                          AS id_asignacion,
    m.nombre                      AS profesor,
    mat.nombre_materia            AS materia,
    g.nombre_grado                AS grado,
    p.nombre                      AS periodo,
    COUNT(e.id)                   AS total_evaluaciones,
    ROUND(AVG(e.actitudinal), 2)  AS promedio_actitudinal,
    ROUND(AVG(e.actividades), 2)  AS promedio_actividades,
    ROUND(AVG(e.metodologia), 2)  AS promedio_metodologia
FROM asignaciones a
JOIN maestros  m   ON m.id   = a.id_profesor
JOIN materias  mat ON mat.id = a.id_materia
JOIN grados    g   ON g.id_grado = a.id_grado
JOIN periodos  p   ON p.id   = a.id_periodo
LEFT JOIN evaluaciones e ON e.id_asignacion = a.id
GROUP BY a.id, m.nombre, mat.nombre_materia, g.nombre_grado, p.nombre;