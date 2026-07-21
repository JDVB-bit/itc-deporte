-- El corte: se ejecuta cuando la interfaz nueva sustituye a la vieja.
--
-- Todo lo demás (`esquema.sql`, `permisos.sql`) puede aplicarse con el sistema
-- viejo funcionando, porque las tablas nuevas conviven con las suyas. Esto no:
-- borra las tablas de las que depende `data.py`, así que **la aplicación vieja
-- deja de funcionar en cuanto se ejecute**.
--
-- Requisito previo: que la interfaz nueva ya esté desplegada y comprobada.

begin;

-- `logros` es el único nombre que se repite entre los dos esquemas, y por eso
-- no se pudo crear antes. El histórico anterior se descarta, como el resto.
drop table if exists logros;

create table logros (
    id          bigserial primary key,
    deporte_id  text references deportes (id),
    anio        integer not null,
    descripcion text not null check (length(trim(descripcion)) > 0)
);

alter table logros enable row level security;
create policy "lectura publica" on logros for select using (true);
create policy "solo admin" on logros
    for all using (es_admin()) with check (es_admin());

-- Las tablas del sistema anterior. A partir de aquí no hay vuelta atrás sin
-- respaldo.
drop table if exists llaves;
drop table if exists partidos;
drop table if exists partidos_inter;
drop table if exists jugadores;
drop table if exists equipos;
drop table if exists sorteos;

-- `usuarios` sale por separado: sus credenciales ya no valen porque la
-- autenticación pasa a Supabase Auth. Comprobar que cada persona que deba
-- entrar tiene su cuenta creada ANTES de ejecutar esto.
drop table if exists usuarios;

commit;
