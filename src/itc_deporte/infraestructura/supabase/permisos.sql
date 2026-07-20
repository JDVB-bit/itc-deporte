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
