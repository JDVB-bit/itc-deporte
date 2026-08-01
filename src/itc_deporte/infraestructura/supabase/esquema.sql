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
