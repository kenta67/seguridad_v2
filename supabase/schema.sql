create extension if not exists "pgcrypto";

create table if not exists perfiles_usuarios (
    id uuid primary key
        references auth.users(id)
        on delete cascade,
    nombres varchar(120) not null,
    apellidos varchar(120) not null,
    email varchar(200) unique not null,
    usuario varchar(50) unique not null,
    contrasena text not null,
    numero varchar(15),
    foto_perfil_url text,
    rol varchar(20) not null
        check (rol in ('PADREs', 'HIJOs')),
    activo boolean default true,
    ultimo_login timestamp,
    created_at timestamp default now()
);

create table if not exists eventos_sospechosos (
    id uuid primary key default gen_random_uuid(),
    tipo_evento varchar(50) not null,
    descripcion text,
    confianza decimal(5,2),
    nivel_riesgo varchar(20)
        check (nivel_riesgo in ('BAJO', 'MEDIO', 'ALTO', 'CRITICO')),
    imagen_evidencia_url text,
    video_evidencia_url text,
    atendido boolean default false,
    fecha_evento timestamp default now()
);

create table if not exists alertas (
    id uuid primary key default gen_random_uuid(),
    evento_id uuid references eventos_sospechosos(id) on delete cascade,
    usuario_id uuid references perfiles_usuarios(id) on delete cascade,
    titulo varchar(150),
    mensaje text,
    leida boolean default false,
    created_at timestamp default now()
);

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

alter table perfiles_usuarios enable row level security;
alter table eventos_sospechosos enable row level security;
alter table alertas enable row level security;
alter table logs_sistema enable row level security;
alter table configuraciones enable row level security;

create policy "usuarios leen su perfil"
on perfiles_usuarios for select
to authenticated
using (auth.uid() = id);

create policy "usuarios leen eventos"
on eventos_sospechosos for select
to authenticated
using (true);

create policy "usuarios leen alertas propias"
on alertas for select
to authenticated
using (auth.uid() = usuario_id);

create policy "usuarios leen configuraciones propias"
on configuraciones for select
to authenticated
using (auth.uid() = usuarios_id);

