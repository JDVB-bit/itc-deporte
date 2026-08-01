-- PASO 2 de la Fase 7. Pegar entero en el SQL Editor de Supabase y ejecutar.
-- Es esquema.sql + permisos.sql en un solo archivo, en el orden correcto.
-- No borra nada. La aplicacion actual sigue funcionando despues de esto.
--
-- GENERADO: no editar a mano. `tests/infraestructura/test_esquema.py`
-- comprueba que siga coincidiendo con los dos ficheros de origen.

-- Esquema objetivo del motor de competiciones.
--
-- Deriva del dominio ya estabilizado (Fases 1-3), no al revés. Todavía NO se
-- aplica: la migración con backfill es la Fase 7, y hasta entonces la
-- aplicación sigue operando sobre las tablas antiguas.
--
-- El cambio de fondo respecto del esquema vigente es que el enfrentamiento deja
-- de ser el texto "Nombre (Curso) vs Nombre (Curso)" y pasa a referenciar
-- participantes por id. Con eso desaparecen el parseo con expresiones regulares
-- y la rutina de limpieza de filas corruptas que lo acompañaba.
--
-- Las concesiones y las políticas RLS viven en `permisos.sql`, que se aplica
-- justo después: activar RLS sin políticas dejaría las tablas inaccesibles, así
-- que las dos cosas van juntas o no van.

-- ── Catálogo ────────────────────────────────────────────────────────────────

create table deportes (
    id     text primary key,
    nombre text not null check (length(trim(nombre)) > 0),
    icono  text not null default ''
);

-- ── Competición ─────────────────────────────────────────────────────────────

create table competiciones (
    id         text primary key,
    nombre     text not null check (length(trim(nombre)) > 0),
    deporte_id text not null references deportes (id),
    temporada  text,
    estado     text not null default 'Borrador'
               check (estado in ('Borrador', 'En curso', 'Finalizada')),
    -- Sistema de puntuación, criterios de desempate y calendario:
    -- {"puntuacion": {...}, "desempate": [...], "calendario": {...}}.
    reglas     jsonb not null default '{}'::jsonb
);

-- Jerárquica: la categoría PRIMERA es la división padre de 601, 602…
-- En otra institución podrían ser sedes, edades o pesos.
create table divisiones (
    id             text not null,
    competicion_id text not null references competiciones (id) on delete cascade,
    nombre         text not null check (length(trim(nombre)) > 0),
    padre_id       text,
    primary key (competicion_id, id),
    foreign key (competicion_id, padre_id) references divisiones (competicion_id, id),
    check (padre_id is distinct from id)
);

create table participantes (
    id             text primary key,
    competicion_id text not null references competiciones (id) on delete cascade,
    division_id    text,
    nombre         text not null check (length(trim(nombre)) > 0),
    foreign key (competicion_id, division_id) references divisiones (competicion_id, id)
);

create index participantes_por_competicion on participantes (competicion_id);

-- Antes: la tabla `jugadores`, que repetía categoría, deporte, curso y equipo
-- como texto en cada fila.
create table miembros (
    id              text primary key,
    participante_id text not null references participantes (id) on delete cascade,
    nombre          text not null check (length(trim(nombre)) > 0),
    dorsal          integer check (dorsal >= 0)
);

create index miembros_por_participante on miembros (participante_id);

-- ── Fases ───────────────────────────────────────────────────────────────────

create table fases (
    id             text not null,
    competicion_id text not null references competiciones (id) on delete cascade,
    tipo           text not null check (tipo in ('grupos', 'eliminatoria')),
    nombre         text not null check (length(trim(nombre)) > 0),
    orden          integer not null check (orden >= 0),
    -- Solo para eliminatorias: cuántos participantes entran al cuadro.
    -- Sustituye al tope de 16 que estaba fijado en el código.
    cupos          integer check (cupos >= 2),
    fixture        text not null default 'round_robin',
    -- {"vueltas": 1, "jornadas_forzadas": 7} — las 7 jornadas del ITC dejan de
    -- ser un número mágico y pasan a ser configuración explícita.
    config_fixture jsonb not null default '{}'::jsonb,
    primary key (competicion_id, id),
    unique (competicion_id, orden)
);

create table grupos (
    id             text not null,
    competicion_id text not null,
    fase_id        text not null,
    nombre         text not null check (length(trim(nombre)) > 0),
    primary key (competicion_id, fase_id, id),
    foreign key (competicion_id, fase_id) references fases (competicion_id, id)
             on delete cascade
);

-- La clave única sobre (fase, participante) impone en la base la misma
-- invariante que `FaseDeGrupos` impone en memoria: nadie está en dos grupos de
-- la misma fase.
create table inscripciones_en_grupo (
    competicion_id  text not null,
    fase_id         text not null,
    grupo_id        text not null,
    participante_id text not null references participantes (id) on delete cascade,
    primary key (competicion_id, fase_id, grupo_id, participante_id),
    unique (competicion_id, fase_id, participante_id),
    foreign key (competicion_id, fase_id, grupo_id)
        references grupos (competicion_id, fase_id, id) on delete cascade
);

-- ── Enfrentamientos ─────────────────────────────────────────────────────────

create table enfrentamientos (
    id             text primary key,
    competicion_id text not null,
    fase_id        text not null,
    grupo_id       text,
    -- Fase de grupos: `jornada`. Eliminatoria: `ronda` y `slot`.
    jornada        integer check (jornada >= 1),
    ronda          integer check (ronda >= 0),
    slot           integer check (slot >= 0),
    local_id       text references participantes (id) on delete restrict,
    visitante_id   text references participantes (id) on delete restrict,
    fecha          timestamptz,
    estado         text not null default 'Pendiente'
                   check (estado in ('Pendiente', 'Finalizado')),
    foreign key (competicion_id, fase_id) references fases (competicion_id, id)
             on delete cascade,
    foreign key (competicion_id, fase_id, grupo_id)
        references grupos (competicion_id, fase_id, id) on delete set null,
    -- Nadie se enfrenta a sí mismo. En el esquema anterior esto no era
    -- expresable, porque los dos lados vivían dentro de la misma cadena.
    check (local_id is null or visitante_id is null or local_id <> visitante_id),
    -- Las casillas vacías del cuadro son legítimas mientras no se sepa quién
    -- las ocupa; en la fase de grupos ambos lados están siempre definidos.
    check (ronda is not null or (local_id is not null and visitante_id is not null))
);

create index enfrentamientos_por_fase on enfrentamientos (competicion_id, fase_id);
create unique index enfrentamientos_por_casilla
    on enfrentamientos (competicion_id, fase_id, ronda, slot)
    where ronda is not null;

create table marcadores (
    enfrentamiento_id text primary key
                      references enfrentamientos (id) on delete cascade,
    -- El total decide el partido: goles en fútbol, sets ganados en voleibol.
    total_local       integer not null check (total_local >= 0),
    total_visitante   integer not null check (total_visitante >= 0),
    -- Detalle opcional: [{"local": 25, "visitante": 20}, …]. Es lo que hace
    -- expresable el voleibol, que antes se puntuaba por goles y admitía empates.
    parciales         jsonb not null default '[]'::jsonb
);

-- `logros` no se declara aquí: choca con la tabla del mismo nombre que el
-- sistema viejo sigue usando. Se crea en `corte.sql`, cuando se retire.


----------------------------------------------------------------------------

-- Concesiones y políticas RLS. Se aplica después de `esquema.sql`.
--
-- La autorización de verdad vive en la capa de servicio (`aplicacion/permisos.py`),
-- que es donde se comprueba y donde está probada. Esto es la **segunda línea**:
-- si alguien alcanzara la API REST de Supabase saltándose la aplicación, RLS
-- sigue en medio. Las dos capas dicen lo mismo a propósito.
--
-- Depende de Supabase Auth: `auth.uid()` es el usuario del JWT. Es la razón por
-- la que se sustituye la tabla `usuarios` con bcrypt propio, que no tenía forma
-- de hacerse visible dentro de Postgres.
--
-- Aplicado y comprobado: las tablas, funciones e índices se crean sin error.
--
-- Lo que NO está comprobado es el **comportamiento** de las políticas. La suite
-- de contrato corre con la clave `service_role`, que salta RLS por completo, de
-- modo que nada de lo que pasa demuestra que estas políticas permitan o nieguen
-- lo que deben. Eso lo comprueba `tests/contratos/test_rls.py`, que necesita
-- además la clave `anon`.
--
-- `logros` y su política viven en `corte.sql`: esa tabla choca con la del
-- sistema viejo, así que solo puede crearse cuando aquella se retire.

-- ── Concesiones ─────────────────────────────────────────────────────────────

create table concesiones (
    usuario_id     uuid not null references auth.users (id) on delete cascade,
    -- NULL = alcance global. Solo el admin lo tiene.
    competicion_id text references competiciones (id) on delete cascade,
    rol            text not null check (rol in ('registrador', 'admin')),
    otorgada_en    timestamptz not null default now(),
    -- `nulls not distinct` hace que dos concesiones globales del mismo usuario
    -- colisionen, que es lo que se quiere: sin ello, NULL != NULL las dejaría
    -- duplicarse.
    unique nulls not distinct (usuario_id, competicion_id),
    -- Las mismas invariantes que impone `Concesion` en memoria.
    check (rol <> 'registrador' or competicion_id is not null),
    check (rol <> 'admin' or competicion_id is null)
);

create index concesiones_por_usuario on concesiones (usuario_id);
create index concesiones_por_competicion on concesiones (competicion_id);

-- ── Funciones de apoyo ──────────────────────────────────────────────────────
-- `security definer` para que puedan leer `concesiones` sin quedar atrapadas en
-- la propia política que definen. `search_path` fijado para que no se las pueda
-- redirigir a un esquema plantado por otro.

create function es_admin() returns boolean
    language sql stable security definer set search_path = public as $$
    select exists (
        select 1 from concesiones
        where usuario_id = auth.uid() and rol = 'admin'
    );
$$;

create function puede_registrar(comp text) returns boolean
    language sql stable security definer set search_path = public as $$
    select es_admin() or exists (
        select 1 from concesiones
        where usuario_id = auth.uid()
          and rol = 'registrador'
          and competicion_id = comp
    );
$$;

-- ── Políticas ───────────────────────────────────────────────────────────────
-- Leer es público: un visitante consulta tablas, resultados y cuadros sin
-- identificarse. Escribir exige concesión.

alter table deportes       enable row level security;
alter table competiciones  enable row level security;
alter table divisiones     enable row level security;
alter table participantes  enable row level security;
alter table miembros       enable row level security;
alter table fases          enable row level security;
alter table grupos         enable row level security;
alter table inscripciones_en_grupo enable row level security;
alter table enfrentamientos enable row level security;
alter table marcadores     enable row level security;
alter table concesiones    enable row level security;

create policy "lectura publica" on deportes       for select using (true);
create policy "lectura publica" on competiciones  for select using (true);
create policy "lectura publica" on divisiones     for select using (true);
create policy "lectura publica" on participantes  for select using (true);
create policy "lectura publica" on miembros       for select using (true);
create policy "lectura publica" on fases          for select using (true);
create policy "lectura publica" on grupos         for select using (true);
create policy "lectura publica" on inscripciones_en_grupo for select using (true);
create policy "lectura publica" on enfrentamientos for select using (true);
create policy "lectura publica" on marcadores     for select using (true);

-- Solo el admin toca el catálogo y la estructura de las competiciones.
create policy "solo admin" on deportes      for all using (es_admin()) with check (es_admin());
create policy "solo admin" on competiciones for all using (es_admin()) with check (es_admin());
create policy "solo admin" on divisiones    for all using (es_admin()) with check (es_admin());
create policy "solo admin" on fases         for all using (es_admin()) with check (es_admin());
create policy "solo admin" on grupos        for all using (es_admin()) with check (es_admin());

-- El registrador escribe participantes y resultados, solo en lo suyo.
create policy "registrador de la competicion" on participantes
    for all using (puede_registrar(competicion_id))
    with check (puede_registrar(competicion_id));

create policy "registrador de la competicion" on miembros
    for all using (
        exists (
            select 1 from participantes p
            where p.id = participante_id and puede_registrar(p.competicion_id)
        )
    )
    with check (
        exists (
            select 1 from participantes p
            where p.id = participante_id and puede_registrar(p.competicion_id)
        )
    );

-- Sortear es del admin, pero cargar resultados es del registrador. Como ambas
-- cosas escriben en `enfrentamientos`, la política admite a los dos y es la capa
-- de servicio la que distingue una operación de la otra.
create policy "registrador de la competicion" on enfrentamientos
    for all using (puede_registrar(competicion_id))
    with check (puede_registrar(competicion_id));

create policy "registrador de la competicion" on marcadores
    for all using (
        exists (
            select 1 from enfrentamientos e
            where e.id = enfrentamiento_id and puede_registrar(e.competicion_id)
        )
    )
    with check (
        exists (
            select 1 from enfrentamientos e
            where e.id = enfrentamiento_id and puede_registrar(e.competicion_id)
        )
    );

create policy "registrador de la competicion" on inscripciones_en_grupo
    for all using (puede_registrar(competicion_id))
    with check (puede_registrar(competicion_id));

-- Las concesiones las reparte el admin. Cada cual puede ver las suyas, para que
-- la interfaz sepa qué ofrecerle.
create policy "ver las propias" on concesiones
    for select using (usuario_id = auth.uid() or es_admin());

create policy "solo admin reparte" on concesiones
    for all using (es_admin()) with check (es_admin());
