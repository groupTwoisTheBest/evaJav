# Plan: Botón "Editar" profesor con htmx (edición inline de nombre)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que el botón "Editar" de la tabla de profesores funcione con htmx reemplazando la fila por un formulario inline que solo edita el nombre, igual que el patrón de estudiantes.

**Architecture:** Replicar el flujo htmx de estudiantes: botón `hx-get` que intercambia la `<tr>` por un template parcial, `hx-put` para guardar y un endpoint de cancelar con `HX-Redirect`. Backend en FastAPI (`app/vistas.py` + `app/repositorio.py` + `app/esquemas.py`), frontend en Jinja2.

**Tech Stack:** FastAPI, Jinja2, asyncpg, HTMX, Pydantic.

**Spec:** `docs/superpowers/specs/2026-10-28-editar-profesor-inline-htmx-design.md`

## Global Constraints

- Editar **solo el nombre** del profesor (decisión del usuario).
- Seguir el patrón existente de `gestionEstudiantes` (ya probado en el proyecto).
- **Orden de rutas:** `GET /gestionProfesores/cancelar` DEBE declararse antes de `GET /gestionProfesores/{id}` en `vistas.py`, si no `{id: int}` la captura → 422.
- Proyecto sin lint/typecheck; **sin framework de tests** (AGENTS.md: "No hay tests", pytest requiere PostgreSQL vivo). La verificación es manual con `uvicorn main:app --reload` + navegador.
- `DATABASE_URL` y `JWT_SECRET` en `.env` para arrancar.

## Review Focus

- **Fila tras guardar:** el swap debe devolver la fila con las clases badge originales (`ok`/`off`/`vivo` según valores), o la fila se verá distinta tras guardar.
- **ID inexistente:** `GET .../editar` y `PUT .../guardar` con ID que no existe en `maestros` deben responder `HX-Redirect` al listado (no 500 ni fila rota).
- **Nombre vacío:** el schema `GuardarProfesor` debe rechazar nombre vacío (min_length=1) — verificar que el input del partial tiene `required` y el schema valida.
- **Orden de rutas:** verificar que `GET /gestionProfesores/cancelar` no devuelve 422 (capturada por `{id: int}`).
- **Duplicado `/gestionProfesores/nuevo`:** ya existen dos rutas GET para esa URL (líneas 318 y 418 de `vistas.py`); no tocar, pero no introducir duplicados nuevos para `editar`/`guardar`.

---

### Task 1: Backend — schema y funciones de repositorio

**Files:**
- Modify: `app/esquemas.py` (agregar después de `GuardarEstudiante`, línea ~23)
- Modify: `app/repositorio.py` (agregar al final del archivo)

**Interfaces:**
- Consumes: conexión `asyncpg.Connection` (patrón de las funciones existentes del archivo).
- Produces: `GuardarProfesor` (modelo Pydantic con campo `nombre`), `detalle_por_profesor(conn, id_profesor: int) -> dict | None`, `actualizar_profesor(conn, id_profesor: int, nombre: str) -> dict | None`. Task 2 importa estos tres por nombre.

- [ ] **Step 1: Agregar `GuardarProfesor` en `app/esquemas.py`**

Igual que `GuardarEstudiante` pero solo con nombre:

```python
class GuardarProfesor(BaseModel):
    nombre: Annotated[str, Field(min_length=1, max_length=100)]
```

- [ ] **Step 2: Agregar `detalle_por_profesor` en `app/repositorio.py`**

Misma consulta que `obtener_todos_los_profesores` (línea 555) pero con `WHERE m.id = $1` y sin `GROUP BY`/`ORDER BY`. Devuelve dict con claves `id`, `nombre`, `grados_asignados`, `promedio_eval`, `estado` (estado calculado igual: `"Activo" if promedio >= 4.0 else "Alerta"`). Retorna `None` si no hay fila.

- [ ] **Step 3: Agregar `actualizar_profesor` en `app/repositorio.py`**

Firmar `async def actualizar_profesor(conn, id_profesor: int, nombre: str) -> dict | None`, con `UPDATE maestros SET nombre = $2 WHERE id = $1 RETURNING *`, retornando `dict(row) if row else None` (patrón de `actualizarectudiante`).

- [ ] **Step 4: Verificar que los archivos compilan**

Run: `python -c "import app.esquemas, app.repositorio"`
Expected: sale sin errores.

- [ ] **Step 5: Commit**

```bash
git add app/esquemas.py app/repositorio.py
git commit -m "feat: agregar schema y funciones de repo para editar profesor"
```

---

### Task 2: Backend — rutas htmx en `app/vistas.py`

**Files:**
- Modify: `app/vistas.py` (imports línea 32-44; sección "GESTIÓN DE PROFESORES" línea 413+)

**Interfaces:**
- Consumes: `GuardarProfesor`, `detalle_por_profesor`, `actualizar_profesor` (de Task 1); `HX-Redirect` (header, patrón ya usado en el archivo).
- Produces: rutas `GET /gestionProfesores/cancelar`, `GET /gestionProfesores/{id}/editar`, `PUT /gestionProfesores/{id}/guardar` (consumidas por el frontend de Task 3).

- [ ] **Step 1: Actualizar imports en `app/vistas.py`**

Agregar `detalle_por_profesor, actualizar_profesor` al import de `app.repositorio` (línea 32-40) y `GuardarProfesor` al de `app.esquemas` (línea 41-44).

- [ ] **Step 2: Reemplazar el stub `GET /gestionProfesores/{id}/editar` (línea 444)**

Ahora recibe `conn: ConnectionDep`, llama a `detalle_por_profesor(conn, id)`. Si es `None`, retorna `Response(status_code=200, headers={"HX-Redirect": "/gestionProfesores"})`. Si existe, renderiza `gestionProfesoresForm_editar.html` con `context={"profesor": profesor}`.

- [ ] **Step 3: Reemplazar el stub `POST /gestionProfesores/{id}/editar` (línea 453) por `PUT /gestionProfesores/{id}/guardar`**

Firmar `async def guardar_profesor(request: Request, conn: ConnectionDep, datos: Annotated[GuardarProfesor, Form()], id: int)`. Llama `actualizar_profesor(conn, id, datos.nombre)`; retorna `Response(status_code=303, headers={"HX-Redirect": "/gestionProfesores"})` (mismo patrón que `actualizar_estudiante`).

- [ ] **Step 4: Agregar `GET /gestionProfesores/cancelar` ANTES de `GET /gestionProfesores/{id}` (línea 435)**

Insertar la ruta justo antes de `ver_profesor`. Retorna `Response(status_code=303, headers={"HX-Redirect": "/gestionProfesores"})` (clon de `cancelar_edicion`, línea 345). **Posición crítica:** antes de la ruta `{id}`.

- [ ] **Step 5: Verificar que la app arranca y las rutas existen**

Run: `python -c "import app.vistas"` y luego arrancar `uvicorn main:app --reload` y abrir `http://127.0.0.1:8000/docs` — verificar que aparecen `GET /gestionProfesores/cancelar`, `GET /gestionProfesores/{id}/editar`, `PUT /gestionProfesores/{id}/guardar`, y que ya no existe `POST /gestionProfesores/{id}/editar`.

- [ ] **Step 6: Commit**

```bash
git add app/vistas.py
git commit -m "feat: rutas htmx para editar/guardar/cancelar profesor"
```

---

### Task 3: Frontend — template parcial y botón htmx

**Files:**
- Create: `templates/gestionProfesoresForm_editar.html`
- Modify: `templates/gestionProfesores.html:34` (el `<a>` de Editar)

**Interfaces:**
- Consumes: rutas de Task 2 y claves del dict de `detalle_por_profesor` (`id`, `nombre`, `grados_asignados`, `promedio_eval`, `estado`).
- Produces: comportamiento visible del flujo completo (verificado en Task 4).

- [ ] **Step 1: Crear `templates/gestionProfesoresForm_editar.html`**

Una `<tr>` con 5 celdas — clonar la estructura y clases de la fila de `gestionProfesores.html` (líneas 31-40), reemplazando la celda del nombre por `<input type="text" value="{{ profesor.nombre }}" class="input" name="nombre" required>` y la de acciones por los botones htmx:

```html
<button hx-put="/gestionProfesores/{{ profesor.id }}/guardar" hx-include="closest tr" hx-target="closest tr" hx-swap="outerHTML" class="btn sm ghost">guardar</button>
<button hx-get="/gestionProfesores/cancelar" class="btn sm ghost">cancelar</button>
```

Las celdas de grado/promedio/estado replican las badges condicionales de la lista (`{% if profesor.promedio_eval >= 3.5 %}ok{% else %}off{% endif %}` y `{% if profesor.estado == 'Activo' %}ok vivo{% else %}off{% endif %}`) para que la fila se vea idéntica tras el swap. El archivo NO lleva `{% extends %}` ni `<table>` — es un fragmento parcial (igual que `gestionEstudianteForm_editar.html`).

- [ ] **Step 2: Cambiar el `<a>` de Editar en `gestionProfesores.html` por botón htmx**

Reemplazar:

```html
<a href="/gestionProfesores/{{ teacher.id }}/editar" class="btn sm ghost">Editar</a>
```

por:

```html
<button hx-get="/gestionProfesores/{{ teacher.id }}/editar" hx-target="closest tr" hx-swap="outerHTML" class="btn sm ghost">Editar</button>
```

- [ ] **Step 3: Commit**

```bash
git add templates/gestionProfesoresForm_editar.html templates/gestionProfesores.html
git commit -m "feat: formulario inline htmx para editar nombre de profesor"
```

---

### Task 4: Verificación manual del flujo completo

**Files:** ninguno (solo verificación; si algo falla, corregir en el archivo correspondiente).

- [ ] **Step 1: Arrancar la app**

Run: `uvicorn main:app --reload` con `.env` válido (BD viva). Login como administrador, ir a `/gestionProfesores`.

- [ ] **Step 2: Probar editar → guardar**

Clic "Editar" en una fila → la fila se convierte en input con el nombre actual + botones guardar/cancelar (sin recarga de página). Cambiar el nombre, clic "guardar" → la fila vuelve a modo vista con el nombre nuevo, y al recargar la página el cambio persiste en la BD.

- [ ] **Step 3: Probar cancelar**

Clic "Editar" en otra fila, cambiar el texto sin guardar, clic "cancelar" → redirige al listado sin cambios persistidos.

- [ ] **Step 4: Probar borde — ID inexistente**

Con el servidor corriendo, pedir `GET /gestionProfesores/99999/editar` (curl o directo en la barra de dirección con header HX si se desea) → responde redirect a `/gestionProfesores` (no 500).

- [ ] **Step 5: Probar borde — nombre vacío**

Editar una fila, borrar todo el nombre, guardar → el navegador bloquea el envío por el `required` del input (no se hace request). Si se fuerza el request, Pydantic responde 422 (validación del schema).

- [ ] **Step 6: Commit final si hubo correcciones**

```bash
git add -A
git commit -m "fix: correcciones de verificación del editor de profesores"
```
