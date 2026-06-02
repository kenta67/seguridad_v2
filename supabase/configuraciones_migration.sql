create table if not exists configuraciones (
    id uuid primary key default gen_random_uuid(),
    usuarios_id uuid references perfiles_usuarios(id) on delete cascade,
    deteccion_personas boolean default true,
    deteccion_armas boolean default true,
    deteccion_armas_blancas boolean default true,
    deteccion_rostro_cubierto boolean default true,
    grabacion_automatica boolean default true,
    notificaciones_push boolean default true,
    created_at timestamp default now()
);

create unique index if not exists configuraciones_usuarios_id_key
on configuraciones(usuarios_id);

alter table configuraciones enable row level security;

drop policy if exists "usuarios leen configuraciones propias" on configuraciones;
create policy "usuarios leen configuraciones propias"
on configuraciones for select
to authenticated
using (auth.uid() = usuarios_id);

drop policy if exists "usuarios crean configuraciones propias" on configuraciones;
create policy "usuarios crean configuraciones propias"
on configuraciones for insert
to authenticated
with check (auth.uid() = usuarios_id);

drop policy if exists "usuarios actualizan configuraciones propias" on configuraciones;
create policy "usuarios actualizan configuraciones propias"
on configuraciones for update
to authenticated
using (auth.uid() = usuarios_id)
with check (auth.uid() = usuarios_id);
