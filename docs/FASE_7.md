# Fase 7 — Aplicar el esquema nuevo

Lo que hay que hacer a mano. **Nada de esto lo he ejecutado yo**: no tengo
credenciales de tu base, y no debería tenerlas.

La idea de fondo: los pasos 1–4 se pueden hacer **con la aplicación vieja
funcionando**. Las tablas nuevas conviven con las suyas y no se pisan. El corte
—retirar las viejas— no es parte de esta fase: va después de la Fase 8, cuando
haya una interfaz nueva que las sustituya.

---

## Paso 0 — Respaldo

Aunque no se migra nada, se van a crear once tablas y activar RLS. Un respaldo
cuesta un minuto.

En Supabase: **Database → Backups**, o bien `pg_dump` si prefieres tenerlo local.

## Paso 1 — Hazlo primero en un proyecto de pruebas

Esto es lo que más te recomiendo de todo el documento. Crea un proyecto nuevo en
Supabase (el plan gratuito sirve) y aplica ahí los pasos 2 y 3 antes de tocar el
de verdad.

Motivo: los repositorios que escribí **nunca se han ejecutado**. Si tienen un
fallo, prefieres encontrarlo en una base vacía.

## Paso 2 — Aplicar el esquema

En el **SQL Editor** de Supabase, pega y ejecuta en este orden:

1. `src/itc_deporte/infraestructura/supabase/esquema.sql`
2. `src/itc_deporte/infraestructura/supabase/permisos.sql`

El orden importa: las políticas RLS del segundo referencian las tablas del
primero.

Si algo falla a medias, `drop table` de lo que se haya creado y vuelve a
empezar; no hay estado intermedio que valga la pena rescatar.

### Qué NO crea

`logros`. Esa tabla existe con el mismo nombre en el sistema viejo y con otra
forma, así que crearla ahora rompería la aplicación actual. Vive en `corte.sql`
y se crea cuando la vieja se retire.

## Paso 3 — Crear el primer administrador

Hay un problema de huevo y gallina que conviene conocer antes de chocarse con
él: la política RLS de `concesiones` dice que solo un admin puede repartir
concesiones, y ser admin **es** tener una fila en `concesiones`. El primer admin
no puede crearse desde la aplicación.

Se resuelve desde el panel, que usa la clave `service_role` y salta RLS:

1. **Authentication → Users → Add user**, con tu correo.
2. Copia el UUID que te asigna.
3. En el SQL Editor:

```sql
insert into concesiones (usuario_id, rol, competicion_id)
values ('PEGA-AQUI-EL-UUID', 'admin', null);
```

Comprueba que quedó bien:

```sql
select es_admin();   -- debería dar false: el SQL Editor no actúa como tú
select * from concesiones;
```

A partir de ahí, ese admin puede repartir el resto de concesiones desde la
aplicación.

## Paso 4 — Correr los tests contra la instancia

Este es el paso que convierte "escrito con cuidado" en "funciona":

```bash
SUPABASE_URL=https://tu-proyecto.supabase.co \
SUPABASE_KEY=tu-service-role-key \
venv/Scripts/python -m pytest -m supabase
```

Son 44 tests de contrato. Corren contra los repositorios de Supabase exactamente
las mismas comprobaciones que ya pasan contra los de memoria.

**Usa la clave `service_role`, no la `anon`.** Los tests escriben y borran, y con
`anon` RLS los bloqueará. Y por lo mismo: hazlo en el proyecto de pruebas, porque
la fixture `limpiar` **borra el contenido de las tablas** antes y después de cada
test.

### Si fallan

Es el resultado más probable, y está bien. Pásame la salida y lo arreglo: para
eso existen esos tests. Lo que no quiero es que construyamos la interfaz encima
sin haberlos corrido.

---

## Después (no es Fase 7)

- **Fase 8** — la interfaz nueva sobre los servicios.
- **El corte** — `corte.sql` retira las tablas viejas y crea `logros`. Rompe la
  aplicación anterior, así que va cuando la nueva ya esté desplegada y
  comprobada. Antes de ejecutarlo, verifica que **todas** las personas que deban
  entrar tienen su cuenta en Supabase Auth: `usuarios` desaparece con sus
  contraseñas.

## Resumen

| Paso | Dónde | Rompe algo |
|---|---|---|
| 0 · Respaldo | Panel de Supabase | no |
| 1 · Proyecto de pruebas | Panel de Supabase | no |
| 2 · `esquema.sql` + `permisos.sql` | SQL Editor | no |
| 3 · Primer admin | Panel + SQL Editor | no |
| 4 · `pytest -m supabase` | Terminal | borra las tablas nuevas |
| — · `corte.sql` | tras la Fase 8 | **sí, la app vieja** |
