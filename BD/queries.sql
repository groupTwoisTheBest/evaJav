-- Nombres y Apellidos
SELECT *
FROM "BD"
WHERE "id_estudiante" IN (
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
    WHERE "nombre" = 'Packages'
);

-- Agregar un nuevo estudiante
INSERT INTO "Estudiante" ("Nombre", "Apellido", "D_Identidad")
VALUES ('Jony', 'Hernandez', '1032013457');

-- Agregar un nuevo maestro 
INSERT INTO "maestro" ("Nombre", "Apellido")
VALUES ('Jovanny', 'Velez');

-- Eliminar un estudiante
DELETE FROM "id_estudiante"
WHERE "Nombre" = 'Jony'
AND "id" NOT IN (
    SELECT DISTINCT "id_estudiante" 
    FROM "BD"
);