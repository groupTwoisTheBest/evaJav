-- Nombres y Apellidos
SELECT *
FROM "BD"
WHERE "Estudiante_id" IN (
    SELECT "id"
    FROM "Estudiante"
    WHERE "Nombre" = 'Jony'
    AND "Apellido" = 'Hernandez'
);

SELECT * 
FROM "BD"
WHERE "problema_id" = (
    SELECT "id"
    FROM "problemas"
    WHERE "name" = 'Packages'
);

-- Agregar un nuevo estudiante
INSERT INTO "Estudiante" ("Nombre", "Apellido", "D_Identidad")
VALUES ('Jony', 'Hernandez', '1032013457');

-- Agregar un nuevo Profesor
INSERT INTO "Profesor" ("Nombre", "Apellido")
VALUES ('Jovanny', 'Velez');

-- Eliminar un estudiante
DELETE FROM "Estudiante"
WHERE "Nombre" = 'Jony'
AND "id" NOT IN (
    SELECT DISTINCT "Estudiante_id" 
    FROM "BD"
);