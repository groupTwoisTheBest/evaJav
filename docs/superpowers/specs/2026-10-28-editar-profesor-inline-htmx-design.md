# Diseño: Botón "Editar" profesor con htmx (edición inline de nombre)

Fecha: 2026-10-28

## Intención y por qué

El botón "Editar" en `templates/gestionProfesores.html` es hoy un `<a href>` que apunta a un stub que renderiza `gestionProfesoresForm.html`, un template **inexistente** → el botón está roto. Se quiere que funcione con htmx igual que el de estudiantes: al hacer clic, la fila de la tabla se convierte en inputs editables inline, con "guardar" y "cancelar", sin recargar la página entera.

## Metas

- Botón Editar de profesores funcione con htmx (`hx-get` → reemplaza la fila por un formulario).
- Editar **solo el nombre** del profesor (decisión del usuario; email/especialidad existen en la BD pero no se muestran en la tabla).
- Guardar persiste el nombre en la tabla `maestros` y refresca la fila.
- Cancelar vuelve al listado sin guardar.

## No-metas (fuera de alcance)

- Editar grado asignado (es many-to-many vía `asignaciones`, calculado) o promedio/estado (calculados).
- El botón "Eliminar" de profesores (sigue sin acción, no se pidió).
- Arreglar otros stubs (`editar-grado`, duplicado de `/gestionProfesores/nuevo`, etc.).

## Restricciones

- Replicar el patrón existente de `gestionEstudiantes` (template parcial `<tr>`, `hx-target="closest tr"`, `hx-swap="outerHTML"`).
- **Orden de rutas:** la nueva ruta `GET /gestionProfesores/cancelar` debe definirse **antes** de `GET /gestionProfesores/{id}`, si no, `{id: int}` la captura y falla con 422.
- Proyecto sin lint/typecheck ni tests; verificar manualmente con `uvicorn main:app --reload`.

## Enfoques considerados

1. **Intercambio de fila con htmx (elegido)** — mismo patrón que estudiantes: un template parcial renderiza la `<tr>` editable; "guardar" hace `hx-put`, "cancelar" redirige. Es lo pedido ("parecido a gestión de estudiantes") y reutiliza la infraestructura ya probada.
2. Página completa de edición — no encaja: pide htmx inline, y el stub actual ya intenta eso y falla.
3. Modal con htmx — más trabajo (CSS/JS nuevo) y rompe la paridad con estudiantes.

## Decisiones

- **Template parcial nuevo** `templates/gestionProfesoresForm_editar.html`: `<tr>` con input `name="nombre"` + celdas de grado/promedio/estado replicando las clases badge de la lista (para que la fila se vea idéntica tras el swap) + botones guardar/cancelar.
- **Rutas** en `app/vistas.py` (reemplazan stubs):
  - `GET /gestionProfesores/{id}/editar` → carga profesor desde BD y renderiza el parcial. Si no existe, responde con header `HX-Redirect: /gestionProfesores`.
  - `PUT /gestionProfesores/{id}/guardar` → valida con schema y actualiza; responde `HX-Redirect: /gestionProfesores` (igual que estudiantes).
  - `GET /gestionProfesores/cancelar` → responde 303 con `HX-Redirect: /gestionProfesores`. Va antes de `GET /gestionProfesores/{id}`.
- **Repositorio** (`app/repositorio.py`), siguiendo el estilo de los de estudiantes:
  - `detalle_por_profesor(conn, id)` → misma consulta de `obtener_todos_los_profesores` con `WHERE m.id = $1`; devuelve `{id, nombre, grados_asignados, promedio_eval, estado}`.
  - `actualizar_profesor(conn, id, nombre)` → `UPDATE maestros SET nombre=$2 WHERE id=$1 RETURNING *`.
- **Schema** (`app/esquemas.py`): `GuardarProfesor` con `nombre: str` (`min_length=1`, `max_length=100`), igual que `GuardarEstudiante`.
- **Template lista** (`gestionProfesores.html`): el `<a>` se reemplaza por `<button hx-get="/gestionProfesores/{{ teacher.id }}/editar" hx-target="closest tr" hx-swap="outerHTML" class="btn sm ghost">Editar</button>`.
- El stub `POST /gestionProfesores/{id}/editar` se reemplaza por el nuevo `PUT .../guardar` (el stub no hacía nada y apuntaba al template inexistente).
- **Llamada del builder:** si el ID no existe al guardar, responder también con `HX-Redirect` al listado (evita fila rota).

## Lo que queda para el builder

Implementar los cambios anteriores en los 3 archivos de backend + 2 templates, y verificar manualmente en el navegador: editar nombre → guardar (persiste y recarga lista), cancelar (vuelve sin cambios), y que el resto de la fila (grado/promedio/estado) se siga viendo igual.
