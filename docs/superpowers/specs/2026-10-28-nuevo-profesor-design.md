# Diseño — Apartado "Nuevo profesor"

Fecha: 2026-10-28
Estado: aprobado por el usuario

## Intención

El admin crea un profesor escribiendo solo el nombre; materias, grados y
periodo se cargan desde la base de datos y se eligen con botones que
marcan/desmarcan sin recargar (HTMX).

## Qué se guarda (producto cruzado confirmado por el usuario)

1. `INSERT INTO maestros (nombre)` → `id`.
2. Cada materia marcada × cada grado marcado → una fila en
   `asignaciones (id_profesor, id_materia, id_grado, id_periodo)`, todas
   con el periodo elegido. Todo dentro de una transacción.
3. Por cada asignación creada, se inscriben automáticamente los
   estudiantes existentes de ese grado:
   `INSERT INTO inscripciones (id_estudiante, id_asignacion) ... ya_voto = false`
   con `ON CONFLICT (id_estudiante, id_asignacion) DO NOTHING`.

## Decisiones tomadas

- Selector de periodo: se muestran TODOS los periodos con su estado
  (`nombre (abierto|cerrado)`), no solo los abiertos.
- Las listas salen de tres funciones nuevas en `app/repositorio.py`:
  `listar_materias`, `listar_grados`, `listar_periodos`.
- Rutas: se reescriben los stubs reales en `/gestionProfesores/nuevo`
  (GET carga listas; POST guarda). Se elimina la ruta GET duplicada
  muerta (apunta a `gestionProfesoresForm.html`, que no existe).
- Selección HTMX: patrón "toggle server-side". Cada chip es un `<button>`
  con `hx-post` + `hx-target="this"` + `hx-swap="outerHTML"`; el servidor
  devuelve el mismo botón con/sin clase `selected` y, si está seleccionado,
  con un `<input type="hidden">` dentro (válido: hidden no es contenido
  interactivo). El estado vive en el DOM y el `POST` del formulario
  recolecta los hidden inputs. El selector único de periodo apunta al
  grupo completo (`hx-target="#periodos-chips"`), que el servidor vuelve
  a renderizar con un solo chip activo.
- Los atributos `hx-vals` se generan con `| tojson` (escapa seguido para
  atributos y evita romper JSON con nombres con tildes/comillas).

## No-objetivos

- No se toca la ruta vieja `POST /nuevo-maestro` ni `registrar_maestro()`
  (insertan columnas que no existen en el esquema actual; queda pendiente
  un refactor aparte).
- No se implementa edición/eliminación de profesores (los stubs siguen).
- No se agregan tests (el proyecto no tiene infraestructura de tests; la
  verificación es manual con la app corriendo).

## Restricciones del esquema (tablas y columnas reales, sin inventar)

- `maestros(id, nombre)` — nombre es `varchar(60)`.
- `materias(id, nombre_materia)`, `grados(id_grado, nombre_grado)`,
  `periodos(id, nombre, fecha_inicio, fecha_fin, estado)`.
- `asignaciones(id, id_profesor, id_materia, id_periodo, id_grado)` con
  UNIQUE `(id_profesor, id_materia, id_grado, id_periodo)`.
- `inscripciones(id, id_estudiante, id_asignacion, ya_voto)` con UNIQUE
  `(id_estudiante, id_asignacion)`.
