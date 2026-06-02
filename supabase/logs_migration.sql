create table if not exists logs_sistema (
    id bigint generated always as identity primary key,
    usuario_id uuid references perfiles_usuarios(id) on delete set null,
    accion varchar(150) not null,
    descripcion text,
    ip_address varchar(80),
    user_agent text,
    resultado varchar(50),
    created_at timestamp default now()
);

create index if not exists logs_sistema_created_at_idx
on logs_sistema(created_at desc);

alter table logs_sistema enable row level security;

drop policy if exists "padres leen logs del sistema" on logs_sistema;
create policy "padres leen logs del sistema"
on logs_sistema for select
to authenticated
using (
    exists (
        select 1
        from perfiles_usuarios
        where perfiles_usuarios.id = auth.uid()
          and perfiles_usuarios.rol = 'PADREs'
    )
);
