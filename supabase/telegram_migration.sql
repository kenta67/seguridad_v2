alter table perfiles_usuarios
add column if not exists telegram_chat_id varchar(80);
