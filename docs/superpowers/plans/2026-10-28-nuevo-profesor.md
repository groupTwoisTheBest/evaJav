# Plan de implementación — Apartado "Nuevo profesor"

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** El admin crea un profesor (solo nombre) y elige materias y grados con botones multi-selección y un periodo con botón de selección única, todo cargado desde la BD y con toggle HTMX sin recargar.

**Architecture:** Tres funciones de catálogo + una función `guardar_maestro()` (transacción: maestro → producto cruzado de `asignaciones` → `inscripciones` de estudiantes existentes) en `app/repositorio.py`. Las rutas `/gestionProfesores/nuevo` (GET/POST) y dos endpoints HTMX de toggle viven en `app/vistas.py`. La plantilla `gestionProfesoresNuevo.html` renderiza chips con `for` Jinja2 usando partials reutilizables (`chip.html`, `periodosChips.html`); el estado de selección vive en el DOM (clase `selected` + hidden input dentro del botón).

**Tech Stack:** FastAPI + Jinja2 + asyncpg + HTMX 4.0.0 (ya cargado en `baseAdministrador.html`).

**Spec:** `docs/superpowers/specs/2026-10-28-nuevo-profesor-design.md` (diseño aprobado el 2026-10-28; las preguntas de relación profesor-materia-grado e inscripciones ya fueron respondidas por el usuario).

## Global Constraints

- Usar SOLO estas tablas/columnas (existentes en `BD/schema.sql`): `maestros(id, nombre varchar(60))`, `materias(id, nombre_materia)`, `grados(id_grado, nombre_grado)`, `periodos(id, nombre, estado)`, `asignaciones(id, id_profesor, id_materia, id_periodo, id_grado)`, `inscripciones(id, id_estudiante, id_asignacion, ya_voto)`.
- Estilo del código: `async`/`await` con `asyncpg`, docstrings en español como el resto de `vistas.py`, secciones comentadas en `repositorio.py` con el mismo formato (`# ── Título ──...`).
- NO tocar la ruta vieja `POST /nuevo-maestro`, el schema `CrearMaestro` ni `registrar_maestro()` (quedan como están; refactor aparte).
- El formulario NO lleva email ni contraseña (la tabla `maestros` no tiene esas columnas).
- HTMX ya está incluido en `templates/baseAdministrador.html` (unpkg htmx 4.0.0); no agregar otros CDNs.
- El proyecto no tiene infraestructura de tests (AGENTS.md: "No hay tests"). La verificación de cada tarea es: chequeo de importación + revisión visual/funcional con `uvicorn main:app --reload` y SQL de control.
- No hay linter/formatter configurado; seguir el estilo del archivo que se modifica.

## Review Focus

- Enviar el formulario sin seleccionar nada → se debe re-renderizar con mensaje de error, no devolver 422 ni 500 (validación manual en el POST porque `materias`/`grados`/`periodo` pueden venir vacíos).
- Nombres de materias con tildes/comillas → `hx-vals` debe generarse con `| tojson` para no romper el JSON del atributo.
- Selector de periodo: al hacer clic en otro periodo, el chip anterior debe desmarcarse (el endpoint devuelve el grupo completo con un solo `activo`).
- `inscripciones`: estudiantes sin inscripción previa en esas asignaciones → `ON CONFLICT (id_estudiante, id_asignacion) DO NOTHING` para no reventar con duplicados.
- Ruta GET duplicada `/gestionProfesores/nuevo` (la de la sección "GESTIÓN DE PROFESORES", que renderiza `gestionProfesoresForm.html`, inexistente) → eliminarla para que no quede código muerto que oculta a la real; verificar que la app arranca tras el borrado.
- Manipulación de ids inválidos en el POST (FK inexistente) → el POST envuelve `guardar_maestro()` en `try/except` y re-renderiza con error genérico en vez de 500.

---

### Task 1: Funciones de catálogo en `app/repositorio.py`

**Files:**
- Modify: `app/repositorio.py` (añadir sección nueva al final del archivo)

**Interfaces:**
- Consumes: conexión `asyncpg.Connection` inyectada (patrón existente del archivo).
- Produces (lo usan las tareas 3 y 4):
  - `async def listar_materias(conn) -> list[dict]` → filas `{id, nombre_materia}` ordenadas por `nombre_materia`.
  - `async def listar_grados(conn) -> list[dict]` → filas `{id_grado, nombre_grado}` ordenadas por `id_grado`.
  - `async def listar_periodos(conn) -> list[dict]` → filas `{id, nombre, estado}` ordenadas por `id DESC`.

- [ ] **Step 1: Añadir la sección de catálogos al final de `repositorio.py`**

Con el formato de comentario del archivo (`# ── Título ──…`), tres funciones que hacen `conn.fetch` con los `SELECT` exactos del bloque Produces y devuelven `[dict(row) for row in rows]` (mismo patrón que `select_profesor`).

- [ ] **Step 2: Verificar importación**

Run: `python -c "import app.repositorio; print(app.repositorio.listar_materias, app.repositorio.listar_grados, app.repositorio.listar_periodos)"`
Expected: imprime las tres funciones sin error.

- [ ] **Step 3: Commit**

```bash
git add app/repositorio.py
git commit -m "feat: añadir listar_materias, listar_grados y listar_periodos en repositorio"
```

---

### Task 2: `guardar_maestro()` en `app/repositorio.py`

**Files:**
- Modify: `app/repositorio.py` (continuar la sección nueva)

**Interfaces:**
- Consumes: Task 1 (no directamente, misma conexión).
- Produces (lo usa Task 3):
  `async def guardar_maestro(conn, nombre: str, materias: list[int], grados: list[int], id_periodo: int) -> int`
  → devuelve el `id` del maestro creado; lanza `ValueError` si `materias` o `grados` vienen vacíos.

- [ ] **Step 1: Implementar `guardar_maestro()`**

Lógica (dentro de `async with conn.transaction():`, mismo patrón que `registrar_estudiante`):
1. `id_profesor = await conn.fetchval("INSERT INTO maestros (nombre) VALUES ($1) RETURNING id", nombre.strip())`.
2. Bucle doble `for id_materia in materias: for id_grado in grados:` → `fetchval` de
   `INSERT INTO asignaciones (id_profesor, id_materia, id_grado, id_periodo) VALUES ($1,$2,$3,$4) RETURNING id`.
3. Por cada asignación creada:
   `INSERT INTO inscripciones (id_estudiante, id_asignacion) SELECT id, $2 FROM estudiantes WHERE id_grado = $1 ON CONFLICT (id_estudiante, id_asignacion) DO NOTHING` con `(id_grado, id_asignacion)`.
4. `return id_profesor`.

- [ ] **Step 2: Verificar importación**

Run: `python -c "import app.repositorio; print(app.repositorio.guardar_maestro)"`
Expected: imprime la función sin error.

- [ ] **Step 3: Commit**

```bash
git add app/repositorio.py
git commit -m "feat: guardar_maestro crea maestro, asignaciones (producto cruzado) e inscripciones"
```

---

### Task 3: Rutas GET + endpoints HTMX de toggle en `app/vistas.py`

**Files:**
- Modify: `app/vistas.py` (imports; helper; sección "GESTIÓN DE PROFESORES")

**Interfaces:**
- Consumes: Task 1 (`listar_materias`, `listar_grados`, `listar_periodos`). Importarlas en el bloque `from app.repositorio import (...)` existente.
- Produces (lo usan Tasks 4 y 5):
  - `async def _form_nuevo_profesor(request, conn, error: str | None = None)` → helper que consulta las tres listas y devuelve `templates.TemplateResponse(request=request, name="gestionProfesoresNuevo.html", context={"materias": …, "grados": …, "periodos": …, "error": error})`.
  - `GET /gestionProfesores/nuevo` → reescribe el handler existente (`read_gestion_profesores_nuevo`, ~línea 316) para que reciba `conn: ConnectionDep` y devuelva `await _form_nuevo_profesor(request, conn)`.
  - `POST /gestionProfesores/nuevo/chip` → `async def chip_materia_grado(request: Request, tipo: Annotated[str, Form()], id: Annotated[int, Form()], nombre: Annotated[str, Form()], seleccionado: Annotated[bool, Form()])`. Devuelve `templates.TemplateResponse(request=request, name="chip.html", context={"tipo": tipo, "id": id, "nombre": nombre, "seleccionado": not seleccionado})`.
  - `POST /gestionProfesores/nuevo/periodo` → `async def chip_periodo(request: Request, conn: ConnectionDep, id: Annotated[int, Form()])`. Consulta `listar_periodos(conn)` y devuelve `TemplateResponse(name="periodosChips.html", context={"periodos": …, "activo": id})`.

- [ ] **Step 1: Añadir imports de las funciones de catálogo**

Añadir `listar_materias, listar_grados, listar_periodos` al bloque `from app.repositorio import (…)` existente.

- [ ] **Step 2: Reescribir el GET `/gestionProfesores/nuevo` real (~línea 316)**

Cuerpo: `return await _form_nuevo_profesor(request, conn)`. Mantener el nombre del handler y el docstring (actualizarlo brevemente: carga materias, grados y periodos desde la BD).

- [ ] **Step 3: Añadir el helper `_form_nuevo_profesor`**

Justo encima del GET. Misma lógica que el GET con las tres consultas, pero accesible también desde el POST de la Task 5 para re-renderizar con `error`.

- [ ] **Step 4: Añadir los dos endpoints de chip**

Cuerpos exactos del bloque Produces. Comentario de sección `# ============ HTMX: chips de selección ============`.

- [ ] **Step 5: Eliminar la ruta GET duplicada muerta**

Borrar el segundo `@router.get("/gestionProfesores/nuevo")` con handler `nuevo_profesor_form` (sección "GESTIÓN DE PROFESORES", renderiza `gestionProfesoresForm.html`, plantilla inexistente). No borrar nada más de esa sección (los demás stubs de `{id}` quedan).

- [ ] **Step 6: Verificar importación y que FastAPI registra las rutas**

Run: `python -c "import app.vistas; [print(r.path, r.methods) for r in app.vistas.router.routes if 'nuevo' in r.path]"`
Expected: aparece UN solo `GET /gestionProfesores/nuevo`, más `POST /gestionProfesores/nuevo/chip`, `POST /gestionProfesores/nuevo/periodo` y `POST /gestionProfesores/nuevo` (el stub de la Task 5 aún sin implementar).

- [ ] **Step 7: Commit**

```bash
git add app/vistas.py
git commit -m "feat: rutas GET y endpoints HTMX para el formulario nuevo profesor"
```

---

### Task 4: Plantilla y partials de chips

**Files:**
- Create: `templates/chip.html`
- Create: `templates/periodosChips.html`
- Modify: `templates/gestionProfesoresNuevo.html` (reescribir completo)
- Modify: `static/administrador.css` (añadir estilos `.chip`)

**Interfaces:**
- Consumes: contexto `{materias, grados, periodos, error}` de la Task 3; variables Jinja `tipo, id, nombre, seleccionado` (chip.html) y `periodos, activo` (periodosChips.html).
- Produces: el HTML que los endpoints de la Task 3 devuelven; nombres de campos del formulario: `nombre` (text), `materias` (hidden, repetido), `grados` (hidden, repetido), `periodo` (hidden, único).

- [ ] **Step 1: Crear `templates/chip.html` (partial de un chip multi-selección)**

```html
<button type="button" class="chip{% if seleccionado %} selected{% endif %}"
        hx-post="/gestionProfesores/nuevo/chip"
        hx-vals='{{ {"tipo": tipo, "id": id, "nombre": nombre, "seleccionado": seleccionado} | tojson }}'
        hx-target="this" hx-swap="outerHTML">
    {{ nombre }}
    {% if seleccionado %}<input type="hidden" name="{{ tipo }}s" value="{{ id }}">{% endif %}
</button>
```

- [ ] **Step 2: Crear `templates/periodosChips.html` (partial del grupo de periodo)**

Contenedor `<div id="periodos-chips">` con `{% for p in periodos %}` que por cada periodo renderiza un botón `chip` (clase `selected` solo si `activo == p.id`), con `hx-post="/gestionProfesores/nuevo/periodo"`, `hx-vals='{{ {"id": p.id} | tojson }}'`, `hx-target="#periodos-chips"`, `hx-swap="outerHTML"`, etiqueta `{{ p.nombre }} ({{ p.estado }})` y, solo cuando está activo, `<input type="hidden" name="periodo" value="{{ p.id }}">`.

- [ ] **Step 3: Reescribir `templates/gestionProfesoresNuevo.html`**

- `{% extends "baseAdministrador.html" %}` y block title "Nuevo Profesor" como ahora.
- `<form action="/gestionProfesores/nuevo" method="POST">` con:
  - Label + `<input class="input" type="text" name="nombre" maxlength="60" required>`.
  - Bloque "Materias": `<div class="chips">` con `{% for m in materias %}{% with tipo="materia", id=m.id, nombre=m.nombre_materia, seleccionado=false %}{% include "chip.html" %}{% endwith %}{% endfor %}</div>`. Igual para "Grados" con `tipo="grado"`, `g.id_grado`, `g.nombre_grado`.
  - Bloque "Periodo": `{% with activo=None %}{% include "periodosChips.html" %}{% endwith %}`.
  - Botón de envío con la clase `btn` existente y el bloque `{% if error %}` en rojo (mismo estilo que ahora).
- Borrar los campos email/contraseña y el `<select>` de grados hardcodeado.
- Mantener el link "Volver" apuntando a `/gestionProfesores` (el actual apunta a `/gestionEstudiantes`, que es un error).

- [ ] **Step 4: Añadir estilos `.chip` al final de `static/administrador.css`**

Reglas usando las variables del diseño (`--panel-2`, `--line-2`, `--accent`, `--accent-soft`, `--radius`, `--muted`): `.chip` con fondo `--panel-2`, borde `--line-2`, border-radius, cursor pointer y `color: var(--muted)`; `.chip.selected` con fondo `--accent-soft`, borde y texto `--accent`; `.chips { display: flex; flex-wrap: wrap; gap: .5rem; margin-bottom: 1rem; }`. Reutilizar `font: inherit` para heredar tipografía del tema.

- [ ] **Step 5: Verificación visual con la app corriendo**

Run: `uvicorn main:app --reload` → abrir `http://127.0.0.1:8000/gestionProfesores/nuevo`.
Expected: se ven los chips de materias, grados y periodos (con su estado) cargados desde la BD; al hacer clic un chip se marca sin recargar y al volver a clic se desmarca; en periodo, marcar uno desmarca al anterior. Sin consola de errores del navegador.

- [ ] **Step 6: Commit**

```bash
git add templates/chip.html templates/periodosChips.html templates/gestionProfesoresNuevo.html static/administrador.css
git commit -m "feat: plantilla nuevo profesor con chips HTMX y estilos"
```

---

### Task 5: POST real de `/gestionProfesores/nuevo`

**Files:**
- Modify: `app/vistas.py` (reemplazar el stub `crear_profesor`)

**Interfaces:**
- Consumes: Task 2 (`guardar_maestro` — añadir al import de repositorio), Task 3 (`_form_nuevo_profesor`).
- Produces: comportamiento del envío del formulario de la Task 4.

- [ ] **Step 1: Reescribir el stub `POST /gestionProfesores/nuevo`**

```python
@router.post("/gestionProfesores/nuevo")
async def crear_profesor(
    request: Request,
    conn: ConnectionDep,
    nombre: Annotated[str, Form(min_length=1, max_length=60)],
    materias: Annotated[list[int], Form()] = [],
    grados: Annotated[list[int], Form()] = [],
    periodo: Annotated[int | None, Form()] = None,
):
```

Lógica:
1. Si `not materias or not grados or periodo is None` → `return await _form_nuevo_profesor(request, conn, error="Selecciona al menos una materia, un grado y un periodo.")`.
2. `try: await guardar_maestro(conn, nombre.strip(), materias, grados, periodo)` → `return RedirectResponse(url="/gestionProfesores", status_code=status.HTTP_303_SEE_OTHER)`.
3. `except Exception as e:` → `logger.error(...)` y `return await _form_nuevo_profesor(request, conn, error="No se pudo guardar el profesor. Verifica los datos e intenta de nuevo.")`.

- [ ] **Step 2: Añadir `guardar_maestro` al import de `app.repositorio` en `vistas.py`**

- [ ] **Step 3: Verificación funcional completa**

Run: `uvicorn main:app --reload` → en `/gestionProfesores/nuevo`: (a) enviar sin seleccionar nada → mensaje de error, misma página; (b) guardar "Profesor Prueba" con 2 materias × 2 grados y 1 periodo → redirige a `/gestionProfesores` y el profesor aparece en la tabla.
SQL de control en la BD:
```sql
SELECT * FROM maestros ORDER BY id DESC LIMIT 1;
SELECT * FROM asignaciones WHERE id_profesor = <id> ORDER BY id;   -- esperadas: 4 filas
SELECT COUNT(*) FROM inscripciones i JOIN asignaciones a ON a.id = i.id_asignacion
WHERE a.id_profesor = <id>;                                        -- esperadas: estudiantes de los 2 grados × 2 materias
```

- [ ] **Step 4: Commit**

```bash
git add app/vistas.py
git commit -m "feat: POST /gestionProfesores/nuevo guarda profesor con asignaciones e inscripciones"
```
