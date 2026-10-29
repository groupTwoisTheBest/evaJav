# Phase 1: Gestión de Profesores - Datos Reales desde PostgreSQL

## Objective
Replace hardcoded static teacher data in the "Gestión de Profesores" admin page with real teacher data fetched from PostgreSQL using existing routes.

## Tasks

### Task 1: Add `obtener_todos_los_profesores()` in `app/repositorio.py`
- Create async function that queries all teachers from `maestros` table
- Order alphabetically by `nombre`
- Return list of dicts with: id, nombre, email, especialidad

### Task 2: Update `/gestionProfesores` endpoint in `app/vistas.py`
- Call `obtener_todos_los_profesores(connection)`
- Pass teachers list to template context

### Task 3: Replace hardcoded rows in `templates/gestionProfesores.html`
- Remove static HTML table rows
- Add Jinja2 `{% for %}` loop to iterate over teachers
- Keep edit/delete action buttons

### Task 4: Verify with `uvicorn main:app --reload`
- Start server
- Navigate to /gestionProfesores
- Confirm teachers are loaded from database

## Constraints
- No new routes — only modify existing endpoint and template
- Use existing `ConnectionDep` for database access
- Respect existing auth pattern (`CurrentUserDep`)
