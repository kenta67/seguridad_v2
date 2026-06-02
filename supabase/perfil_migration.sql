alter table perfiles_usuarios
add column if not exists foto_perfil_url text;

alter table perfiles_usuarios enable row level security;

drop policy if exists "usuarios actualizan su perfil" on perfiles_usuarios;
create policy "usuarios actualizan su perfil"
on perfiles_usuarios for update
to authenticated
using (auth.uid() = id)
with check (auth.uid() = id);
