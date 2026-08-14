-- ============================================================
-- BASE DE DATOS: Sistema de gestión de estudiantes, maestros,
-- materias, inscripciones y calificaciones.
-- PostgreSQL 18.4
-- ============================================================

-- ------------------------------------------------------------
-- TABLA: Calificaciones
-- Almacena las calificaciones obtenidas por los estudiantes
-- en una relación específica entre profesor y materia.
-- ------------------------------------------------------------
CREATE TABLE public."Calificaciones" (
    -- Identificador único de la calificación.
    id integer NOT NULL,

    -- Identifica la asignación de un profesor a una materia.
    -- Referencia a Profesor_Materia(id).
    id_profesor_materia integer NOT NULL,

    -- Puntuación obtenida.
    -- Actualmente se almacena como texto; sería recomendable
    -- utilizar NUMERIC si representa una calificación numérica.
    puntuacion text,

    -- Fecha y hora en que se registró la calificación.
    fecha timestamp without time zone
);

-- Clave primaria de la tabla de calificaciones.
ALTER TABLE ONLY public."Calificaciones"
    ADD CONSTRAINT "Calificaciones_pkey" PRIMARY KEY (id);

-- Relación entre la calificación y la asignación profesor-materia.
ALTER TABLE ONLY public."Calificaciones"
    ADD CONSTRAINT id_profesor_materia
    FOREIGN KEY (id_profesor_materia)
    REFERENCES public."Profesor_Materia"(id);


-- ------------------------------------------------------------
-- TABLA: Inscripciones
-- Registra las materias en las que está inscrito cada estudiante.
-- ------------------------------------------------------------
CREATE TABLE public."Inscripciones" (
    -- Identificador único de la inscripción.
    id integer NOT NULL,

    -- Estudiante que realiza la inscripción.
    -- Referencia a estudiantes(id).
    id_estudiante integer NOT NULL,

    -- Materia impartida por un profesor en la que se inscribe
    -- el estudiante.
    -- Referencia a Profesor_Materia(id).
    id_profesor_materia integer NOT NULL
);

-- Clave primaria de las inscripciones.
ALTER TABLE ONLY public."Inscripciones"
    ADD CONSTRAINT "Inscripciones_pkey" PRIMARY KEY (id);

-- Relación con el estudiante.
ALTER TABLE ONLY public."Inscripciones"
    ADD CONSTRAINT id_estudiante
    FOREIGN KEY (id_estudiante)
    REFERENCES public.estudiantes(id);

-- Relación con profesor y materia.
ALTER TABLE ONLY public."Inscripciones"
    ADD CONSTRAINT id_profesor_materia
    FOREIGN KEY (id_profesor_materia)
    REFERENCES public."Profesor_Materia"(id);


-- ------------------------------------------------------------
-- TABLA: Profesor_Materia
-- Tabla intermedia que relaciona maestros con materias.
-- Permite saber qué profesor imparte cada materia.
-- ------------------------------------------------------------
CREATE TABLE public."Profesor_Materia" (
    -- Identificador único de la relación.
    id integer NOT NULL,

    -- Profesor encargado de impartir la materia.
    -- Referencia a maestros(id).
    id_profesor integer NOT NULL,

    -- Materia que imparte el profesor.
    -- Referencia a materias(id).
    id_materia integer NOT NULL
);

-- Clave primaria de la relación profesor-materia.
ALTER TABLE ONLY public."Profesor_Materia"
    ADD CONSTRAINT "Profesor_Materia_pkey" PRIMARY KEY (id);

-- Relación con el profesor.
ALTER TABLE ONLY public."Profesor_Materia"
    ADD CONSTRAINT id_profesor
    FOREIGN KEY (id_profesor)
    REFERENCES public.maestros(id);

-- Relación con la materia.
ALTER TABLE ONLY public."Profesor_Materia"
    ADD CONSTRAINT id_materia
    FOREIGN KEY (id_materia)
    REFERENCES public.materias(id);




-- ------------------------------------------------------------
-- TABLA: estudiantes
-- Almacena la información académica y de contacto
-- de los estudiantes.
-- ------------------------------------------------------------
CREATE TABLE public.estudiantes (
    -- Identificador único del estudiante.
    id integer NOT NULL,

    -- Nombre del estudiante.
    nombre character varying(20) NOT NULL,

    -- Contraseña del estudiante.
    -- ADVERTENCIA: debería almacenarse como hash, no como
    -- contraseña directamente.
    contrasenna text NOT NULL,

    -- Correo electrónico del estudiante.
    email text NOT NULL,

    -- Grado académico al que pertenece.
    id_grados integer NOT NULL
);

-- Clave primaria del estudiante.
ALTER TABLE ONLY public.estudiantes
    ADD CONSTRAINT estudiantes_pkey PRIMARY KEY (id);

-- Un grado solamente puede aparecer una vez en esta tabla.
-- Esto implica que actualmente cada grado puede estar asociado
-- a un único estudiante, lo cual probablemente no es lo esperado.
ALTER TABLE ONLY public.estudiantes
    ADD CONSTRAINT estudiantes_id_grados_key UNIQUE (id_grados);

-- Relación entre estudiante y grado.
ALTER TABLE ONLY public.estudiantes
    ADD CONSTRAINT id_grado
    FOREIGN KEY (id_grados)
    REFERENCES public.grados(id);


-- ------------------------------------------------------------
-- TABLA: grados
-- Catálogo de los grados académicos disponibles.
-- ------------------------------------------------------------
CREATE TABLE public.grados (
    -- Identificador único del grado.
    id_grado integer NOT NULL,

    -- Nombre o código del grado.
    -- Ejemplos: '10A', '11B', etc.
    nombre_grado character varying(4) NOT NULL
);

-- Clave primaria del grado.
ALTER TABLE ONLY public.grados
    ADD CONSTRAINT grados_pkey PRIMARY KEY (id_grado);


-- ------------------------------------------------------------
-- TABLA: maestros
-- Catálogo de profesores.
-- ------------------------------------------------------------
CREATE TABLE public.maestros (
    -- Identificador único del profesor.
    id integer NOT NULL,

    -- Nombre del profesor.
    nombre character varying(20) NOT NULL
);

-- Clave primaria del profesor.
ALTER TABLE ONLY public.maestros
    ADD CONSTRAINT maestros_pkey PRIMARY KEY (id);




-- ------------------------------------------------------------
-- TABLA: materias
-- Catálogo de materias disponibles.
-- ------------------------------------------------------------
CREATE TABLE public.materias (
    -- Identificador único de la materia.
    id integer NOT NULL,

    -- Nombre de la materia.
    nombre_materia character varying(20) NOT NULL
);

-- Clave primaria de la materia.
ALTER TABLE ONLY public.materias
    ADD CONSTRAINT materias_pkey PRIMARY KEY (id);

-- No permite registrar dos materias con el mismo nombre.
ALTER TABLE ONLY public.materias
    ADD CONSTRAINT materias_nombre_materia_key
    UNIQUE (nombre_materia);


-- ============================================================
-- RELACIONES PRINCIPALES DEL SISTEMA
-- ============================================================

-- Un estudiante pertenece a un grado.
--
-- estudiantes
--      |
--      | id_grados
--      v
-- grados


-- Un profesor puede impartir una o varias materias.
--
-- maestros
--      |
--      v
-- Profesor_Materia
--      ^
--      |
-- materias


-- Los estudiantes se inscriben en una relación
-- profesor-materia.
--
-- estudiantes
--      |
--      v
-- Inscripciones
--      |
--      v
-- Profesor_Materia


-- Las calificaciones están asociadas a una relación
-- profesor-materia.
--
-- Profesor_Materia
--      |
--      v
-- Calificaciones

