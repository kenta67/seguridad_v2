import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Camera,
  CheckCircle2,
  FlaskConical,
  Eye,
  ImageUp,
  LayoutDashboard,
  Lock,
  LogOut,
  Plus,
  RefreshCw,
  Save,
  Settings,
  Shield,
  Trash2,
  UserRound,
  Users,
  Video,
} from "lucide-react";
import { supabase, supabaseConfigured } from "./lib/supabase";

const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";

const emptyUser = {
  nombres: "",
  apellidos: "",
  email: "",
  usuario: "",
  password: "",
  rol: "HIJOs",
  numero: "",
  activo: true,
};

const navItems = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "usuarios", label: "Usuarios", icon: Users },
  { id: "camaras", label: "Camaras", icon: Camera },
  { id: "eventos", label: "Eventos", icon: AlertTriangle },
  { id: "test", label: "Test IA", icon: FlaskConical },
  { id: "configuracion", label: "Configuracion", icon: Settings },
];

async function apiFetch(path, session, options = {}) {
  const isFormData = options.body instanceof FormData;
  const response = await fetch(`${apiUrl}${path}`, {
    ...options,
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      Authorization: `Bearer ${session.access_token}`,
      ...(options.headers || {}),
    },
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || "Error de servidor");
  }
  return response.json();
}

function Login() {
  const [email, setEmail] = useState("padre1@seguridad.local");
  const [password, setPassword] = useState("Padre12345!");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    const { error: loginError } = await supabase.auth.signInWithPassword({ email, password });
    if (loginError) setError("Credenciales incorrectas o usuario no registrado.");
    setLoading(false);
  }

  if (!supabaseConfigured) return <MissingConfig />;

  return (
    <main className="grid min-h-screen bg-neutral-950 text-neutral-100 lg:grid-cols-[1.05fr_0.95fr]">
      <section className="relative hidden overflow-hidden bg-neutral-900 lg:block">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(16,185,129,0.32),transparent_32%),linear-gradient(135deg,#111827,#020617_62%,#18181b)]" />
        <div className="relative flex h-full flex-col justify-between p-12">
          <div className="flex items-center gap-3">
            <div className="grid h-12 w-12 place-items-center rounded bg-emerald-400 text-neutral-950">
              <Shield size={26} />
            </div>
            <div>
              <h1 className="text-2xl font-semibold">Seguridad V2</h1>
              <p className="text-sm text-neutral-300">Monitoreo inteligente del hogar</p>
            </div>
          </div>
          <div className="max-w-xl">
            <p className="mb-4 text-sm font-medium uppercase tracking-[0.2em] text-emerald-300">YOLOv8 + OpenCV</p>
            <h2 className="text-5xl font-semibold leading-tight">Centro de control para camaras, eventos y usuarios.</h2>
            <div className="mt-8 grid grid-cols-3 gap-3">
              <MetricTile label="Camara local" value="Live" />
              <MetricTile label="Eventos" value="24/7" />
              <MetricTile label="Accesos" value="Roles" />
            </div>
          </div>
          <p className="text-sm text-neutral-400">Sistema local conectado a Supabase.</p>
        </div>
      </section>

      <section className="flex min-h-screen items-center justify-center px-5 py-10">
        <form onSubmit={handleSubmit} className="w-full max-w-md rounded border border-neutral-800 bg-neutral-900 p-6 shadow-2xl">
          <div className="mb-7">
            <div className="mb-4 grid h-12 w-12 place-items-center rounded bg-emerald-400 text-neutral-950">
              <Lock size={24} />
            </div>
            <h2 className="text-2xl font-semibold">Iniciar sesion</h2>
            <p className="mt-1 text-sm text-neutral-400">Acceso para padres e hijos registrados.</p>
          </div>

          <label className="mb-4 block">
            <span className="mb-2 block text-sm text-neutral-300">Correo electronico</span>
            <input className="field" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
          <label className="mb-4 block">
            <span className="mb-2 block text-sm text-neutral-300">Contrasena</span>
            <input className="field" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
          </label>

          {error && <p className="mb-4 rounded border border-red-900 bg-red-950/50 px-3 py-2 text-sm text-red-300">{error}</p>}

          <button className="btn-primary w-full" disabled={loading}>
            <Eye size={18} />
            {loading ? "Validando..." : "Entrar al panel"}
          </button>
        </form>
      </section>
    </main>
  );
}

function MissingConfig() {
  return (
    <main className="grid min-h-screen place-items-center bg-neutral-950 px-6 text-neutral-100">
      <div className="max-w-md rounded border border-neutral-800 bg-neutral-900 p-5">
        <h1 className="mb-2 text-xl font-semibold">Configura Supabase</h1>
        <p className="text-sm text-neutral-300">Revisa `frontend/.env` y coloca una URL Supabase valida y la anon key.</p>
      </div>
    </main>
  );
}

function Dashboard({ session }) {
  const [active, setActive] = useState("dashboard");
  const [profile, setProfile] = useState(null);
  const [events, setEvents] = useState([]);
  const [users, setUsers] = useState([]);
  const [status, setStatus] = useState(null);
  const [userForm, setUserForm] = useState(emptyUser);
  const [editingId, setEditingId] = useState(null);
  const [message, setMessage] = useState("");
  const [testResult, setTestResult] = useState(null);
  const [testLoading, setTestLoading] = useState(false);
  const streamUrl = useMemo(() => `${apiUrl}/camera/stream?t=${Date.now()}`, []);
  const metadataRole = session.user?.user_metadata?.rol;
  const isParent = String(profile?.rol || metadataRole || "").trim().toUpperCase() === "PADRES";

  async function loadProfile() {
    const { data } = await supabase
      .from("perfiles_usuarios")
      .select("nombres, apellidos, email, usuario, rol")
      .eq("id", session.user.id)
      .single();
    setProfile(
      data || {
        nombres: session.user.email?.split("@")[0] || "Usuario",
        apellidos: "",
        email: session.user.email,
        usuario: session.user.user_metadata?.usuario || session.user.email,
        rol: session.user.user_metadata?.rol || "HIJOs",
      },
    );
  }

  async function loadEvents() {
    const { data } = await supabase.from("eventos_sospechosos").select("*").order("fecha_evento", { ascending: false }).limit(30);
    setEvents(data || []);
  }

  async function loadStatus() {
    try {
      const response = await fetch(`${apiUrl}/camera/status`);
      setStatus(await response.json());
    } catch {
      setStatus({ camera_open: false, model_loaded: false, detections: [] });
    }
  }

  async function loadUsers() {
    if (!isParent) return;
    try {
      const data = await apiFetch("/admin/users", session);
      setUsers(data);
    } catch (error) {
      setMessage(`Usuarios: ${error.message}`);
    }
  }

  async function refreshAll() {
    await Promise.all([loadProfile(), loadEvents(), loadStatus()]);
  }

  useEffect(() => {
    refreshAll();
    const timer = setInterval(() => {
      loadEvents();
      loadStatus();
    }, 5000);
    return () => clearInterval(timer);
  }, [session.user.id]);

  useEffect(() => {
    if (isParent) loadUsers();
  }, [isParent]);

  async function logout() {
    await supabase.auth.signOut();
  }

  async function saveUser(event) {
    event.preventDefault();
    setMessage("");
    try {
      if (editingId) {
        const { email, password, ...payload } = userForm;
        await apiFetch(`/admin/users/${editingId}`, session, { method: "PUT", body: JSON.stringify(payload) });
        setMessage("Usuario actualizado.");
      } else {
        await apiFetch("/admin/users", session, { method: "POST", body: JSON.stringify(userForm) });
        setMessage("Usuario creado.");
      }
      setUserForm(emptyUser);
      setEditingId(null);
      loadUsers();
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function removeUser(id) {
    setMessage("");
    try {
      await apiFetch(`/admin/users/${id}`, session, { method: "DELETE" });
      setMessage("Usuario eliminado.");
      loadUsers();
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function attendEvent(id) {
    try {
      await apiFetch(`/admin/events/${id}/attend`, session, { method: "PATCH" });
      loadEvents();
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function testModel(file) {
    if (!file) return;
    setMessage("");
    setTestLoading(true);
    setTestResult(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const endpoint = file.type.startsWith("video/") ? "/test/model/video" : "/test/model/image";
      const result = await apiFetch(endpoint, session, { method: "POST", body: formData });
      setTestResult(result);
    } catch (error) {
      setMessage(`Test IA: ${error.message}`);
    } finally {
      setTestLoading(false);
    }
  }

  const stats = {
    totalEvents: events.length,
    openEvents: events.filter((item) => !item.atendido).length,
    users: users.length || (isParent ? 0 : 1),
    detections: status?.detections?.length || 0,
  };

  return (
    <main className="min-h-screen bg-neutral-950 text-neutral-100">
      <aside className="fixed inset-y-0 left-0 hidden w-72 border-r border-neutral-800 bg-neutral-900 lg:block">
        <div className="flex h-full flex-col">
          <div className="border-b border-neutral-800 p-5">
            <div className="flex items-center gap-3">
              <div className="grid h-11 w-11 place-items-center rounded bg-emerald-400 text-neutral-950">
                <Shield size={24} />
              </div>
              <div>
                <h1 className="font-semibold">Seguridad V2</h1>
                <p className="text-xs text-neutral-400">Panel administrativo</p>
              </div>
            </div>
          </div>
          <nav className="flex-1 space-y-1 p-3">
            {navItems.map((item) => (
              <button key={item.id} onClick={() => setActive(item.id)} className={`nav-item ${active === item.id ? "nav-active" : ""}`}>
                <item.icon size={18} />
                {item.label}
              </button>
            ))}
          </nav>
          <div className="border-t border-neutral-800 p-4">
            <p className="text-sm font-medium">{profile ? `${profile.nombres} ${profile.apellidos}` : "Usuario"}</p>
            <p className="text-xs text-neutral-400">{profile?.rol || "Cargando"}</p>
          </div>
        </div>
      </aside>

      <section className="lg:pl-72">
        <header className="sticky top-0 z-20 border-b border-neutral-800 bg-neutral-950/90 backdrop-blur">
          <div className="flex items-center justify-between px-5 py-4">
            <div>
              <h2 className="text-xl font-semibold">{navItems.find((item) => item.id === active)?.label}</h2>
              <p className="text-sm text-neutral-400">Bienvenido, {profile?.usuario || session.user.email}</p>
            </div>
            <div className="flex items-center gap-2">
              <button className="icon-btn" onClick={refreshAll} title="Actualizar">
                <RefreshCw size={18} />
              </button>
              <button className="icon-btn" onClick={logout} title="Cerrar sesion">
                <LogOut size={18} />
              </button>
            </div>
          </div>
          <div className="flex gap-2 overflow-x-auto px-5 pb-3 lg:hidden">
            {navItems.map((item) => (
              <button key={item.id} onClick={() => setActive(item.id)} className={`mobile-tab ${active === item.id ? "mobile-active" : ""}`}>
                <item.icon size={16} />
                {item.label}
              </button>
            ))}
          </div>
        </header>

        <div className="p-5">
          {message && <div className="mb-4 rounded border border-amber-800 bg-amber-950/30 px-4 py-3 text-sm text-amber-200">{message}</div>}
          {active === "dashboard" && <DashboardHome stats={stats} status={status} events={events} streamUrl={streamUrl} />}
          {active === "usuarios" && (
            <UsersPanel
              isParent={isParent}
              users={users}
              form={userForm}
              setForm={setUserForm}
              editingId={editingId}
              setEditingId={setEditingId}
              saveUser={saveUser}
              removeUser={removeUser}
            />
          )}
          {active === "camaras" && <CamerasPanel status={status} streamUrl={streamUrl} />}
          {active === "eventos" && <EventsPanel events={events} isParent={isParent} attendEvent={attendEvent} />}
          {active === "test" && <TestPanel result={testResult} loading={testLoading} onTest={testModel} />}
          {active === "configuracion" && <SettingsPanel />}
        </div>
      </section>
    </main>
  );
}

function TestPanel({ result, loading, onTest }) {
  const [fileName, setFileName] = useState("");

  function handleFile(event) {
    const file = event.target.files?.[0];
    setFileName(file?.name || "");
    onTest(file);
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[420px_1fr]">
      <section className="panel">
        <PanelHeader icon={FlaskConical} title="Probar modelo YOLO" aside="Sin subir a Supabase" />
        <label className="flex min-h-52 cursor-pointer flex-col items-center justify-center rounded border border-dashed border-neutral-700 bg-neutral-950 p-6 text-center transition hover:border-emerald-500">
          <ImageUp size={34} className="mb-3 text-emerald-300" />
          <span className="font-medium">Cargar foto o video</span>
          <span className="mt-1 text-sm text-neutral-400">Se procesa localmente en FastAPI y no se guarda en Storage.</span>
          <input className="hidden" type="file" accept="image/*,video/*" onChange={handleFile} />
        </label>
        {fileName && <p className="mt-3 text-sm text-neutral-400">Archivo: {fileName}</p>}
        {loading && <p className="mt-3 rounded border border-sky-900 bg-sky-950/40 px-3 py-2 text-sm text-sky-200">Procesando con best.pt...</p>}
      </section>

      <section className="panel">
        <PanelHeader icon={Eye} title="Resultado de prueba" />
        {!result && <EmptyState title="Sin prueba cargada" detail="Selecciona una imagen o video para ver las detecciones." />}
        {result && (
          <div className="space-y-4">
            {(result.annotated_image || result.preview_image) && (
              <img
                src={result.annotated_image || result.preview_image}
                alt="Resultado del modelo"
                className="max-h-[520px] w-full rounded border border-neutral-800 object-contain"
              />
            )}
            {result.type === "video" && (
              <div className="grid gap-3 sm:grid-cols-2">
                <StatusLine label="Frames procesados" value={String(result.frames_processed)} />
                <StatusLine label="Detecciones totales" value={String(result.detections?.length || 0)} />
              </div>
            )}
            {result.summary?.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm font-semibold">Resumen</h4>
                <div className="flex flex-wrap gap-2">
                  {result.summary.map((item) => (
                    <Badge key={item.label}>{item.label}: {item.count}</Badge>
                  ))}
                </div>
              </div>
            )}
            <div>
              <h4 className="mb-2 text-sm font-semibold">Detecciones</h4>
              <div className="max-h-80 overflow-auto rounded border border-neutral-800">
                <table className="w-full min-w-[520px] text-left text-sm">
                  <thead className="border-b border-neutral-800 bg-neutral-950 text-neutral-400">
                    <tr>
                      <th className="px-3 py-2 font-medium">Objeto</th>
                      <th className="px-3 py-2 font-medium">Confianza</th>
                      <th className="px-3 py-2 font-medium">Frame</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-800">
                    {(result.detections || []).map((item, index) => (
                      <tr key={`${item.label}-${index}`}>
                        <td className="px-3 py-2">{item.label}</td>
                        <td className="px-3 py-2">{Math.round(item.confidence * 100)}%</td>
                        <td className="px-3 py-2">{item.frame ?? "-"}</td>
                      </tr>
                    ))}
                    {(result.detections || []).length === 0 && (
                      <tr>
                        <td className="px-3 py-6 text-center text-neutral-400" colSpan="3">Sin detecciones.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}

function DashboardHome({ stats, status, events, streamUrl }) {
  return (
    <div className="space-y-5">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Stat icon={AlertTriangle} label="Eventos recientes" value={stats.totalEvents} tone="red" />
        <Stat icon={Activity} label="Pendientes" value={stats.openEvents} tone="amber" />
        <Stat icon={Users} label="Usuarios" value={stats.users} tone="emerald" />
        <Stat icon={Eye} label="Detecciones activas" value={stats.detections} tone="sky" />
      </div>
      <div className="grid gap-5 xl:grid-cols-[1fr_420px]">
        <section className="panel">
          <PanelHeader icon={Video} title="Camara principal" aside={status?.model_loaded ? "Modelo activo" : "Modelo pendiente"} />
          <CameraFrame streamUrl={streamUrl} />
        </section>
        <section className="panel">
          <PanelHeader icon={AlertTriangle} title="Ultimos eventos" />
          <EventList events={events.slice(0, 6)} compact />
        </section>
      </div>
    </div>
  );
}

function UsersPanel({ isParent, users, form, setForm, editingId, setEditingId, saveUser, removeUser }) {
  if (!isParent) {
    return <EmptyState title="Acceso restringido" detail="Solo los usuarios con rol PADREs pueden administrar usuarios." />;
  }

  function editUser(user) {
    setEditingId(user.id);
    setForm({
      nombres: user.nombres || "",
      apellidos: user.apellidos || "",
      email: user.email || "",
      usuario: user.usuario || "",
      password: "",
      rol: user.rol || "HIJOs",
      numero: user.numero || "",
      activo: Boolean(user.activo),
    });
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[420px_1fr]">
      <form onSubmit={saveUser} className="panel space-y-4">
        <PanelHeader icon={editingId ? Save : Plus} title={editingId ? "Editar usuario" : "Nuevo usuario"} />
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
          <Input label="Nombres" value={form.nombres} onChange={(value) => setForm({ ...form, nombres: value })} />
          <Input label="Apellidos" value={form.apellidos} onChange={(value) => setForm({ ...form, apellidos: value })} />
          <Input label="Correo" type="email" value={form.email} disabled={Boolean(editingId)} onChange={(value) => setForm({ ...form, email: value })} />
          <Input label="Usuario" value={form.usuario} onChange={(value) => setForm({ ...form, usuario: value })} />
          {!editingId && <Input label="Contrasena" type="password" value={form.password} onChange={(value) => setForm({ ...form, password: value })} />}
          <Input label="Telefono" value={form.numero} onChange={(value) => setForm({ ...form, numero: value })} />
          <label className="block">
            <span className="mb-2 block text-sm text-neutral-300">Rol</span>
            <select className="field" value={form.rol} onChange={(event) => setForm({ ...form, rol: event.target.value })}>
              <option value="PADREs">PADREs</option>
              <option value="HIJOs">HIJOs</option>
            </select>
          </label>
          <label className="flex items-center gap-2 text-sm text-neutral-300">
            <input type="checkbox" checked={form.activo} onChange={(event) => setForm({ ...form, activo: event.target.checked })} />
            Usuario activo
          </label>
        </div>
        <div className="flex gap-2">
          <button className="btn-primary" type="submit">
            <Save size={17} />
            Guardar
          </button>
          {editingId && (
            <button className="btn-muted" type="button" onClick={() => { setEditingId(null); setForm(emptyUser); }}>
              Cancelar
            </button>
          )}
        </div>
      </form>

      <section className="panel overflow-hidden">
        <PanelHeader icon={Users} title="Usuarios registrados" aside={`${users.length} usuarios`} />
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="border-b border-neutral-800 text-neutral-400">
              <tr>
                <th className="py-3 pr-4 font-medium">Nombre</th>
                <th className="py-3 pr-4 font-medium">Correo</th>
                <th className="py-3 pr-4 font-medium">Usuario</th>
                <th className="py-3 pr-4 font-medium">Rol</th>
                <th className="py-3 pr-4 font-medium">Estado</th>
                <th className="py-3 text-right font-medium">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-800">
              {users.map((user) => (
                <tr key={user.id}>
                  <td className="py-3 pr-4">{user.nombres} {user.apellidos}</td>
                  <td className="py-3 pr-4 text-neutral-300">{user.email}</td>
                  <td className="py-3 pr-4 text-neutral-300">{user.usuario}</td>
                  <td className="py-3 pr-4"><Badge>{user.rol}</Badge></td>
                  <td className="py-3 pr-4">{user.activo ? "Activo" : "Inactivo"}</td>
                  <td className="py-3">
                    <div className="flex justify-end gap-2">
                      <button className="icon-btn" onClick={() => editUser(user)} title="Editar"><Save size={16} /></button>
                      <button className="icon-btn danger" onClick={() => removeUser(user.id)} title="Eliminar"><Trash2 size={16} /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function CamerasPanel({ status, streamUrl }) {
  return (
    <div className="grid gap-5 xl:grid-cols-[1fr_360px]">
      <section className="panel">
        <PanelHeader icon={Camera} title="Camara de laptop" aside={status?.camera_open ? "En linea" : "Sin acceso"} />
        <CameraFrame streamUrl={streamUrl} />
      </section>
      <section className="panel">
        <PanelHeader icon={Activity} title="Estado tecnico" />
        <div className="space-y-3">
          <StatusLine label="Camara" value={status?.camera_open ? "Conectada" : "No disponible"} />
          <StatusLine label="Modelo YOLO" value={status?.model_loaded ? "Cargado" : "Pendiente"} />
          <StatusLine label="Ruta modelo" value={status?.model_path || "Sin datos"} />
          <StatusLine label="Detecciones" value={String(status?.detections?.length || 0)} />
        </div>
      </section>
    </div>
  );
}

function EventsPanel({ events, isParent, attendEvent }) {
  return (
    <section className="panel">
      <PanelHeader icon={AlertTriangle} title="Eventos sospechosos" aside={`${events.length} registros`} />
      <EventList events={events} isParent={isParent} attendEvent={attendEvent} />
    </section>
  );
}

function SettingsPanel() {
  const options = [
    "Deteccion de personas",
    "Deteccion de armas",
    "Deteccion de armas blancas",
    "Rostro cubierto",
    "Grabacion automatica",
    "Notificaciones push",
  ];
  return (
    <section className="panel max-w-3xl">
      <PanelHeader icon={Settings} title="Configuraciones" aside="Preferencias locales" />
      <div className="grid gap-3 sm:grid-cols-2">
        {options.map((option) => (
          <label key={option} className="flex items-center justify-between rounded border border-neutral-800 bg-neutral-950 px-4 py-3 text-sm">
            <span>{option}</span>
            <input type="checkbox" defaultChecked />
          </label>
        ))}
      </div>
    </section>
  );
}

function CameraFrame({ streamUrl }) {
  return (
    <div className="overflow-hidden rounded border border-neutral-800 bg-black">
      <img src={streamUrl} alt="Camara de seguridad" className="aspect-video w-full object-contain" />
    </div>
  );
}

function EventList({ events, compact = false, isParent = false, attendEvent = () => {} }) {
  if (!events.length) return <EmptyState title="Sin eventos" detail="No hay actividades sospechosas registradas." />;
  return (
    <div className="space-y-3">
      {events.map((event) => (
        <article key={event.id} className="rounded border border-neutral-800 bg-neutral-950 p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="font-semibold">{event.tipo_evento}</h3>
              <p className="text-sm text-neutral-400">{event.descripcion || "Evento detectado por el modelo."}</p>
            </div>
            <Badge tone={event.atendido ? "emerald" : "red"}>{event.atendido ? "Atendido" : event.nivel_riesgo}</Badge>
          </div>
          {!compact && (
            <div className="mt-3 flex flex-wrap items-center justify-between gap-3 text-xs text-neutral-500">
              <span>Confianza: {event.confianza || 0}%</span>
              <span>{new Date(event.fecha_evento).toLocaleString()}</span>
              {isParent && !event.atendido && (
                <button className="btn-muted" onClick={() => attendEvent(event.id)}>
                  <CheckCircle2 size={16} />
                  Marcar atendido
                </button>
              )}
            </div>
          )}
        </article>
      ))}
    </div>
  );
}

function Stat({ icon: Icon, label, value, tone }) {
  return (
    <div className={`stat stat-${tone}`}>
      <div className="flex items-center justify-between">
        <span className="text-sm text-neutral-400">{label}</span>
        <Icon size={18} />
      </div>
      <p className="mt-4 text-3xl font-semibold">{value}</p>
    </div>
  );
}

function PanelHeader({ icon: Icon, title, aside }) {
  return (
    <div className="mb-4 flex items-center justify-between gap-3">
      <div className="flex items-center gap-2">
        <Icon size={19} className="text-emerald-300" />
        <h3 className="font-semibold">{title}</h3>
      </div>
      {aside && <span className="text-xs text-neutral-400">{aside}</span>}
    </div>
  );
}

function StatusLine({ label, value }) {
  return (
    <div className="rounded border border-neutral-800 bg-neutral-950 p-3">
      <p className="text-xs text-neutral-500">{label}</p>
      <p className="mt-1 break-words text-sm text-neutral-200">{value}</p>
    </div>
  );
}

function MetricTile({ label, value }) {
  return (
    <div className="rounded border border-white/10 bg-white/5 p-4">
      <p className="text-xs text-neutral-300">{label}</p>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
    </div>
  );
}

function Input({ label, value, onChange, type = "text", disabled = false }) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm text-neutral-300">{label}</span>
      <input className="field" type={type} value={value} disabled={disabled} onChange={(event) => onChange(event.target.value)} required={!disabled} />
    </label>
  );
}

function Badge({ children, tone = "neutral" }) {
  const colors = {
    neutral: "border-neutral-700 bg-neutral-800 text-neutral-200",
    red: "border-red-900 bg-red-950/60 text-red-200",
    emerald: "border-emerald-900 bg-emerald-950/60 text-emerald-200",
  };
  return <span className={`rounded border px-2 py-1 text-xs font-medium ${colors[tone]}`}>{children}</span>;
}

function EmptyState({ title, detail }) {
  return (
    <div className="rounded border border-neutral-800 bg-neutral-950 p-6 text-center">
      <p className="font-medium">{title}</p>
      <p className="mt-1 text-sm text-neutral-400">{detail}</p>
    </div>
  );
}

export default function App() {
  const [session, setSession] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!supabaseConfigured) {
      setReady(true);
      return;
    }

    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setReady(true);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
      setReady(true);
    });

    return () => subscription.unsubscribe();
  }, []);

  if (!ready) return <div className="grid min-h-screen place-items-center bg-neutral-950 text-neutral-100">Cargando...</div>;
  return session ? <Dashboard session={session} /> : <Login />;
}
