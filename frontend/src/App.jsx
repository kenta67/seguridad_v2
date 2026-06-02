import { useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Camera,
  CheckCircle2,
  FlaskConical,
  Eye,
  ImageUp,
  KeyRound,
  LayoutDashboard,
  Lock,
  LogOut,
  Maximize2,
  MessageCircle,
  Monitor,
  Plus,
  RefreshCw,
  Save,
  Search,
  Settings,
  Shield,
  Trash2,
  UserCheck,
  Users,
  Video,
  X,
} from "lucide-react";
import { supabase, supabaseConfigured } from "./lib/supabase";

const apiUrl = import.meta.env.VITE_API_URL || "http://127.0.0.1:8001";
const apiCandidates = Array.from(
  new Set([apiUrl, "http://127.0.0.1:8001", "http://localhost:8001"]),
);
const imageExtensions = [".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"];
const videoExtensions = [".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".wmv", ".mpeg", ".mpg", ".3gp"];

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
  let lastError = null;

  for (const baseUrl of apiCandidates) {
    try {
      const response = await fetch(`${baseUrl}${path}`, {
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
    } catch (error) {
      lastError = error;
    }
  }

  throw new Error(lastError?.message || "No se pudo conectar con el backend");
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
    <main className="grid min-h-screen bg-[#070b10] text-neutral-100 lg:grid-cols-[1.1fr_0.9fr]">
      <section className="relative hidden overflow-hidden border-r border-neutral-800 bg-neutral-950 lg:block">
        <div className="absolute inset-0 bg-[linear-gradient(135deg,rgba(15,23,42,0.96),rgba(2,6,23,0.94)_48%,rgba(6,78,59,0.72))]" />
        <div className="absolute inset-x-10 top-24 h-px bg-emerald-300/20" />
        <div className="absolute bottom-28 left-12 right-12 grid grid-cols-6 gap-2 opacity-30">
          {Array.from({ length: 24 }).map((_, index) => (
            <div key={index} className="aspect-video rounded border border-white/10 bg-black/40" />
          ))}
        </div>
        <div className="relative flex h-full flex-col justify-between p-12">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="grid h-12 w-12 place-items-center rounded bg-emerald-400 text-neutral-950 shadow-lg shadow-emerald-950">
                <Shield size={26} />
              </div>
              <div>
                <h1 className="text-2xl font-semibold">Seguridad V2</h1>
                <p className="text-sm text-neutral-300">Centro de monitoreo inteligente</p>
              </div>
            </div>
            <span className="rounded border border-emerald-400/40 bg-emerald-400/10 px-3 py-1 text-xs font-medium text-emerald-200">Sistema activo</span>
          </div>
          <div className="max-w-xl">
            <p className="mb-4 text-sm font-medium uppercase tracking-[0.2em] text-emerald-300">YOLOv8 + OpenCV + Supabase</p>
            <h2 className="text-5xl font-semibold leading-tight text-white">Vigilancia, evidencia y usuarios en una sola consola.</h2>
            <p className="mt-5 max-w-lg text-base leading-7 text-neutral-300">
              Panel operativo para supervisar camaras, revisar eventos sospechosos y administrar accesos por rol.
            </p>
            <div className="mt-8 grid grid-cols-3 gap-3">
              <MetricTile label="Video local" value="Live" />
              <MetricTile label="IA" value="best.pt" />
              <MetricTile label="Roles" value="Padre/Hijo" />
            </div>
          </div>
          <div className="flex items-center justify-between text-sm text-neutral-400">
            <span>Conexion local segura</span>
            <span>Backend FastAPI</span>
          </div>
        </div>
      </section>

      <section className="flex min-h-screen items-center justify-center px-5 py-10">
        <form onSubmit={handleSubmit} className="w-full max-w-md rounded border border-neutral-800 bg-neutral-900/95 p-7 shadow-2xl shadow-black/40">
          <div className="mb-7 flex items-start justify-between gap-4">
            <div>
              <div className="mb-4 grid h-12 w-12 place-items-center rounded bg-emerald-400 text-neutral-950">
                <KeyRound size={24} />
              </div>
              <h2 className="text-2xl font-semibold">Iniciar sesion</h2>
              <p className="mt-1 text-sm text-neutral-400">Ingresa con una cuenta registrada del sistema.</p>
            </div>
            <div className="rounded border border-neutral-800 bg-neutral-950 px-3 py-2 text-right">
              <p className="text-xs text-neutral-500">Estado</p>
              <p className="text-sm font-medium text-emerald-300">Online</p>
            </div>
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
            <Lock size={18} />
            {loading ? "Validando..." : "Entrar al panel"}
          </button>
          <p className="mt-4 text-center text-xs text-neutral-500">Acceso auditado por Supabase Auth</p>
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
  const [whatsappStatus, setWhatsappStatus] = useState(null);
  const [cameraTick, setCameraTick] = useState(Date.now());
  const streamUrl = useMemo(() => `${apiUrl}/camera/frame?t=${cameraTick}`, [cameraTick]);
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
    try {
      const data = await apiFetch("/admin/events", session);
      setEvents(data || []);
    } catch (error) {
      setMessage(`Eventos: ${error.message}`);
      setEvents([]);
    }
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

  async function loadWhatsappStatus() {
    if (!isParent) return;
    try {
      setWhatsappStatus(await apiFetch("/admin/whatsapp/status", session));
    } catch (error) {
      setWhatsappStatus({ enabled: false, last_error: { detail: error.message }, recipients: [] });
    }
  }

  async function refreshAll() {
    await Promise.all([loadProfile(), loadEvents(), loadStatus()]);
    if (isParent) loadWhatsappStatus();
  }

  useEffect(() => {
    refreshAll();
    const timer = setInterval(() => {
      loadEvents();
      loadStatus();
    }, 5000);
    const cameraTimer = setInterval(() => setCameraTick(Date.now()), 150);
    return () => {
      clearInterval(timer);
      clearInterval(cameraTimer);
    };
  }, [session.user.id]);

  useEffect(() => {
    if (isParent) {
      loadUsers();
      loadWhatsappStatus();
    }
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

  async function testWhatsapp() {
    setMessage("");
    try {
      const result = await apiFetch("/admin/whatsapp/test", session, {
        method: "POST",
        body: JSON.stringify({ mensaje: "Prueba de WhatsApp desde Seguridad V2" }),
      });
      setMessage(result.sent ? `WhatsApp enviado a ${result.to}.` : "WhatsApp no enviado. Revisa configuracion.");
      loadWhatsappStatus();
    } catch (error) {
      setMessage(`WhatsApp: ${error.message}`);
      loadWhatsappStatus();
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
      const fileName = file.name.toLowerCase();
      const isVideo = file.type.startsWith("video/") || videoExtensions.some((extension) => fileName.endsWith(extension));
      const isImage = file.type.startsWith("image/") || imageExtensions.some((extension) => fileName.endsWith(extension));
      if (!isVideo && !isImage) {
        throw new Error("Formato no soportado. Usa JPG, PNG, WEBP, BMP, TIFF, MP4, MOV, AVI, MKV, WEBM, M4V, WMV, MPEG o 3GP.");
      }
      const endpoint = isVideo ? "/test/model/video" : "/test/model/image";
      const result = await apiFetch(endpoint, session, { method: "POST", body: formData });
      setTestResult(result);
    } catch (error) {
      setMessage(`Test IA: ${error.message}`);
    } finally {
      setTestLoading(false);
    }
  }

  async function testVideoFrame(blob) {
    const formData = new FormData();
    formData.append("file", blob, "video-frame.jpg");
    return apiFetch("/test/model/image", session, { method: "POST", body: formData });
  }

  const stats = {
    totalEvents: events.length,
    openEvents: events.filter((item) => !item.atendido).length,
    users: users.length || (isParent ? 0 : 1),
    detections: status?.detections?.length || 0,
  };

  return (
    <main className="min-h-screen bg-[#070b10] text-neutral-100">
      <aside className="fixed inset-y-0 left-0 hidden w-72 border-r border-neutral-800 bg-[#0d1117] lg:block">
        <div className="flex h-full flex-col">
          <div className="border-b border-neutral-800 p-5">
            <div className="flex items-center gap-3">
              <div className="grid h-11 w-11 place-items-center rounded bg-emerald-400 text-neutral-950 shadow-lg shadow-emerald-950/40">
                <Shield size={24} />
              </div>
              <div>
                <h1 className="font-semibold">Seguridad V2</h1>
                <p className="text-xs text-neutral-400">Command center</p>
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
        <header className="sticky top-0 z-20 border-b border-neutral-800 bg-[#070b10]/90 backdrop-blur">
          <div className="flex items-center justify-between px-5 py-4">
            <div>
              <h2 className="text-xl font-semibold tracking-tight">{navItems.find((item) => item.id === active)?.label}</h2>
              <p className="text-sm text-neutral-400">Operacion activa para {profile?.usuario || session.user.email}</p>
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
          {active === "test" && <TestPanel result={testResult} loading={testLoading} onTest={testModel} onFrameTest={testVideoFrame} />}
          {active === "configuracion" && <SettingsPanel whatsappStatus={whatsappStatus} testWhatsapp={testWhatsapp} />}
        </div>
      </section>
    </main>
  );
}

function TestPanel({ result, loading, onTest, onFrameTest }) {
  const [fileName, setFileName] = useState("");
  const [videoUrl, setVideoUrl] = useState("");
  const [liveResult, setLiveResult] = useState(null);
  const [liveLoading, setLiveLoading] = useState(false);
  const [liveEnabled, setLiveEnabled] = useState(true);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const analyzingRef = useRef(false);
  const activeResult = liveResult || result;
  const totalDetections = activeResult?.detections?.length || 0;
  const averageConfidence = totalDetections
    ? Math.round((activeResult.detections.reduce((sum, item) => sum + item.confidence, 0) / totalDetections) * 100)
    : 0;
  const uniqueLabels = Array.from(new Set((activeResult?.detections || []).map((item) => item.label)));

  useEffect(() => {
    return () => {
      if (videoUrl) URL.revokeObjectURL(videoUrl);
    };
  }, [videoUrl]);

  function handleFile(event) {
    const file = event.target.files?.[0];
    setFileName(file?.name || "");
    setLiveResult(null);

    if (!file) return;
    const lowerName = file.name.toLowerCase();
    const isVideo = file.type.startsWith("video/") || videoExtensions.some((extension) => lowerName.endsWith(extension));

    if (videoUrl) URL.revokeObjectURL(videoUrl);
    if (isVideo) {
      setVideoUrl(URL.createObjectURL(file));
      return;
    }

    setVideoUrl("");
    onTest(file);
  }

  async function analyzeCurrentFrame() {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || !onFrameTest || analyzingRef.current || video.readyState < 2) return;

    analyzingRef.current = true;
    setLiveLoading(true);
    try {
      const width = video.videoWidth || 1280;
      const height = video.videoHeight || 720;
      canvas.width = width;
      canvas.height = height;
      const context = canvas.getContext("2d");
      context.drawImage(video, 0, 0, width, height);
      const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.82));
      if (blob) {
        const nextResult = await onFrameTest(blob);
        setLiveResult({
          ...nextResult,
          type: "video-frame",
          file_name: `${fileName || "video"} @ ${video.currentTime.toFixed(1)}s`,
        });
      }
    } catch {
      // The global message handler already reports upload errors for full-file tests.
    } finally {
      analyzingRef.current = false;
      setLiveLoading(false);
    }
  }

  useEffect(() => {
    if (!videoUrl || !liveEnabled) return undefined;
    const timer = setInterval(() => {
      const video = videoRef.current;
      if (video && !video.paused && !video.ended) analyzeCurrentFrame();
    }, 700);
    return () => clearInterval(timer);
  }, [videoUrl, liveEnabled, fileName]);

  return (
    <div className="space-y-5">
      <section className="grid gap-4 md:grid-cols-3">
        <Stat icon={FlaskConical} label="Detecciones" value={totalDetections} tone="sky" />
        <Stat icon={Activity} label="Confianza media" value={`${averageConfidence}%`} tone="emerald" />
        <Stat icon={Eye} label="Clases detectadas" value={uniqueLabels.length} tone="amber" />
      </section>

      <div className="grid gap-5 xl:grid-cols-[420px_1fr]">
        <section className="panel overflow-hidden p-0">
          <div className="border-b border-neutral-800 bg-neutral-950/70 p-5">
            <PanelHeader icon={FlaskConical} title="Laboratorio IA" aside="Solo pruebas" />
            <p className="text-sm text-neutral-400">Carga una imagen o video para evaluar el modelo sin guardar evidencias.</p>
          </div>
          <div className="space-y-4 p-5">
            <label className="group flex min-h-64 cursor-pointer flex-col items-center justify-center rounded border border-dashed border-neutral-700 bg-neutral-950 p-6 text-center transition hover:border-emerald-500 hover:bg-neutral-900">
              <div className="mb-4 grid h-16 w-16 place-items-center rounded bg-emerald-400/10 text-emerald-300 ring-1 ring-emerald-400/20 transition group-hover:bg-emerald-400 group-hover:text-neutral-950">
                <ImageUp size={34} />
              </div>
              <span className="font-semibold">Seleccionar archivo</span>
              <span className="mt-1 max-w-xs text-sm text-neutral-400">Imagen o video local. En video puedes reproducir, adelantar y retroceder con deteccion del frame actual.</span>
              <input
                className="hidden"
                type="file"
                accept="image/*,video/*,.jpg,.jpeg,.png,.bmp,.webp,.tif,.tiff,.mp4,.mov,.avi,.mkv,.webm,.m4v,.wmv,.mpeg,.mpg,.3gp"
                onChange={handleFile}
              />
            </label>
            <div className="grid gap-3">
              <StatusLine label="Modelo activo" value="best.pt" />
              <StatusLine label="Archivo seleccionado" value={fileName || "Ninguno"} />
              <StatusLine label="Modo de salida" value={videoUrl ? "Video interactivo con deteccion en vivo" : "Deteccion visual sin almacenamiento"} />
            </div>
            {videoUrl && (
              <div className="space-y-3 rounded border border-neutral-800 bg-neutral-950 p-3">
                <label className="flex items-center justify-between gap-3 text-sm text-neutral-300">
                  <span>Deteccion en tiempo real</span>
                  <input type="checkbox" checked={liveEnabled} onChange={(event) => setLiveEnabled(event.target.checked)} />
                </label>
                <button className="btn-muted w-full" type="button" onClick={analyzeCurrentFrame}>
                  <Eye size={16} />
                  Detectar frame actual
                </button>
              </div>
            )}
            {loading && <p className="rounded border border-sky-900 bg-sky-950/40 px-3 py-2 text-sm text-sky-200">Procesando archivo con YOLO...</p>}
            {liveLoading && <p className="rounded border border-emerald-900 bg-emerald-950/40 px-3 py-2 text-sm text-emerald-200">Analizando frame actual...</p>}
          </div>
        </section>

        <section className="panel overflow-hidden p-0">
          <div className="border-b border-neutral-800 bg-neutral-950/70 p-5">
            <PanelHeader icon={Eye} title="Resultado de inferencia" aside={activeResult?.type ? activeResult.type.toUpperCase() : "Esperando archivo"} />
          </div>
          <div className="space-y-5 p-5">
            {videoUrl && (
              <div className="overflow-hidden rounded border border-neutral-800 bg-black">
                <video
                  ref={videoRef}
                  src={videoUrl}
                  controls
                  className="max-h-[460px] w-full bg-black"
                  onLoadedData={analyzeCurrentFrame}
                  onSeeked={analyzeCurrentFrame}
                />
                <canvas ref={canvasRef} className="hidden" />
              </div>
            )}
            {!activeResult && !videoUrl && <EmptyState title="Sin prueba cargada" detail="Selecciona una imagen o video para ver las detecciones." />}
            {activeResult && (
              <>
                {(activeResult.annotated_image || activeResult.preview_image) && (
                  <div className="overflow-hidden rounded border border-neutral-800 bg-black">
                    <img src={activeResult.annotated_image || activeResult.preview_image} alt="Resultado del modelo" className="max-h-[560px] w-full object-contain" />
                  </div>
                )}
                <div className="grid gap-3 md:grid-cols-3">
                  <StatusLine label="Archivo" value={activeResult.file_name || fileName || "-"} />
                  <StatusLine label="Frames procesados" value={String(activeResult.frames_processed || (activeResult.type === "image" || activeResult.type === "video-frame" ? 1 : 0))} />
                  <StatusLine label="Detecciones" value={String(totalDetections)} />
                </div>
                <div>
                  <h4 className="mb-3 text-sm font-semibold">Resumen por clase</h4>
                  {activeResult.summary?.length > 0 ? (
                    <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                      {activeResult.summary.map((item) => (
                        <div key={item.label} className="rounded border border-neutral-800 bg-neutral-950 p-3">
                          <p className="text-sm font-medium">{item.label}</p>
                          <p className="mt-1 text-2xl font-semibold text-emerald-300">{item.count}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="flex flex-wrap gap-2">
                      {uniqueLabels.length > 0 ? uniqueLabels.map((label) => <Badge key={label}>{label}</Badge>) : <Badge>Sin clases</Badge>}
                    </div>
                  )}
                </div>
                <div>
                  <h4 className="mb-3 text-sm font-semibold">Detalle de detecciones</h4>
                  <div className="max-h-80 overflow-auto rounded border border-neutral-800">
                    <table className="w-full min-w-[620px] text-left text-sm">
                      <thead className="border-b border-neutral-800 bg-neutral-950 text-xs uppercase tracking-wide text-neutral-500">
                        <tr>
                          <th className="px-4 py-3 font-medium">Objeto</th>
                          <th className="px-4 py-3 font-medium">Confianza</th>
                          <th className="px-4 py-3 font-medium">Frame</th>
                          <th className="px-4 py-3 font-medium">Caja</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-neutral-800">
                        {(activeResult.detections || []).map((item, index) => (
                          <tr key={`${item.label}-${index}`} className="hover:bg-neutral-950/70">
                            <td className="px-4 py-3"><Badge tone={item.confidence > 0.7 ? "emerald" : "sky"}>{item.label}</Badge></td>
                            <td className="px-4 py-3">{Math.round(item.confidence * 100)}%</td>
                            <td className="px-4 py-3">{item.frame ?? "-"}</td>
                            <td className="px-4 py-3 text-neutral-400">{item.box ? item.box.join(", ") : "-"}</td>
                          </tr>
                        ))}
                        {(activeResult.detections || []).length === 0 && (
                          <tr>
                            <td className="px-4 py-8 text-center text-neutral-400" colSpan="4">Sin detecciones.</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            )}
          </div>
        </section>
      </div>
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
  const [query, setQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState("TODOS");

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

  const normalizedQuery = query.trim().toLowerCase();
  const filteredUsers = users.filter((user) => {
    const matchesQuery = [user.nombres, user.apellidos, user.email, user.usuario, user.rol]
      .filter(Boolean)
      .join(" ")
      .toLowerCase()
      .includes(normalizedQuery);
    const matchesRole = roleFilter === "TODOS" || user.rol === roleFilter;
    return matchesQuery && matchesRole;
  });
  const userStats = {
    total: users.length,
    parents: users.filter((user) => user.rol === "PADREs").length,
    children: users.filter((user) => user.rol === "HIJOs").length,
    active: users.filter((user) => user.activo).length,
  };

  return (
    <div className="space-y-5">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Stat icon={Users} label="Usuarios totales" value={userStats.total} tone="sky" />
        <Stat icon={Shield} label="Padres" value={userStats.parents} tone="emerald" />
        <Stat icon={UserCheck} label="Hijos" value={userStats.children} tone="amber" />
        <Stat icon={Activity} label="Activos" value={userStats.active} tone="emerald" />
      </section>

      <div className="grid gap-5 xl:grid-cols-[430px_1fr]">
        <form onSubmit={saveUser} className="panel overflow-hidden p-0">
          <div className="border-b border-neutral-800 bg-neutral-950/70 p-5">
            <PanelHeader icon={editingId ? Save : Plus} title={editingId ? "Editar usuario" : "Nuevo usuario"} aside={editingId ? "Modo edicion" : "Alta rapida"} />
            <p className="text-sm text-neutral-400">Administra accesos por rol y estado de cuenta.</p>
          </div>
          <div className="space-y-4 p-5">
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
              <Input label="Nombres" value={form.nombres} onChange={(value) => setForm({ ...form, nombres: value })} />
              <Input label="Apellidos" value={form.apellidos} onChange={(value) => setForm({ ...form, apellidos: value })} />
              <Input label="Correo" type="email" value={form.email} disabled={Boolean(editingId)} onChange={(value) => setForm({ ...form, email: value })} />
              <Input label="Usuario" value={form.usuario} onChange={(value) => setForm({ ...form, usuario: value })} />
              {!editingId && <Input label="Contrasena" type="password" value={form.password} onChange={(value) => setForm({ ...form, password: value })} />}
              <Input label="Telefono" value={form.numero} onChange={(value) => setForm({ ...form, numero: value })} />
            </div>

            <div className="rounded border border-neutral-800 bg-neutral-950 p-3">
              <span className="mb-3 block text-sm text-neutral-300">Rol del usuario</span>
              <div className="grid grid-cols-2 gap-2">
                {["PADREs", "HIJOs", "OTROS"].map((role) => (
                  <button
                    key={role}
                    type="button"
                    className={`rounded border px-3 py-2 text-sm transition ${form.rol === role ? "border-emerald-400 bg-emerald-400 text-neutral-950" : "border-neutral-700 bg-neutral-900 text-neutral-300 hover:bg-neutral-800"}`}
                    onClick={() => setForm({ ...form, rol: role })}
                  >
                    {role}
                  </button>
                ))}
              </div>
            </div>

            <label className="flex items-center justify-between rounded border border-neutral-800 bg-neutral-950 px-4 py-3 text-sm text-neutral-300">
              <span>Usuario activo</span>
              <input type="checkbox" checked={form.activo} onChange={(event) => setForm({ ...form, activo: event.target.checked })} />
            </label>

            <div className="flex gap-2">
              <button className="btn-primary flex-1" type="submit">
                <Save size={17} />
                Guardar usuario
              </button>
              {editingId && (
                <button className="btn-muted" type="button" onClick={() => { setEditingId(null); setForm(emptyUser); }}>
                  Cancelar
                </button>
              )}
            </div>
          </div>
        </form>

        <section className="panel overflow-hidden p-0">
          <div className="border-b border-neutral-800 bg-neutral-950/70 p-5">
            <PanelHeader icon={Users} title="Directorio de usuarios" aside={`${filteredUsers.length}/${users.length} visibles`} />
            <div className="mt-4 grid gap-3 lg:grid-cols-[1fr_220px]">
              <label className="relative block">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-500" size={17} />
                <input
                  className="field pl-10"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Buscar por nombre, correo, usuario o rol"
                />
              </label>
              <select className="field" value={roleFilter} onChange={(event) => setRoleFilter(event.target.value)}>
                <option value="TODOS">Todos los roles</option>
                <option value="PADREs">Solo padres</option>
                <option value="HIJOs">Solo hijos</option>
                <option value="OTROS">Solo otros</option>
              </select>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[880px] text-left text-sm">
              <thead className="border-b border-neutral-800 bg-neutral-950 text-xs uppercase tracking-wide text-neutral-500">
                <tr>
                  <th className="px-5 py-3 font-medium">Usuario</th>
                  <th className="px-5 py-3 font-medium">Contacto</th>
                  <th className="px-5 py-3 font-medium">Rol</th>
                  <th className="px-5 py-3 font-medium">Estado</th>
                  <th className="px-5 py-3 font-medium">Creado</th>
                  <th className="px-5 py-3 text-right font-medium">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-800">
                {filteredUsers.map((user) => (
                  <tr key={user.id} className="transition hover:bg-neutral-950/70">
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-3">
                        <div className="grid h-10 w-10 place-items-center rounded bg-neutral-800 text-sm font-semibold text-emerald-300">
                          {`${user.nombres?.[0] || "U"}${user.apellidos?.[0] || ""}`.toUpperCase()}
                        </div>
                        <div>
                          <p className="font-medium text-neutral-100">{user.nombres} {user.apellidos}</p>
                          <p className="text-xs text-neutral-500">@{user.usuario}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-4">
                      <p className="text-neutral-300">{user.email}</p>
                      <p className="text-xs text-neutral-500">{user.numero || "Sin telefono"}</p>
                    </td>
                    <td className="px-5 py-4"><Badge tone={user.rol === "PADREs" ? "emerald" : "sky"}>{user.rol}</Badge></td>
                    <td className="px-5 py-4"><Badge tone={user.activo ? "emerald" : "red"}>{user.activo ? "Activo" : "Inactivo"}</Badge></td>
                    <td className="px-5 py-4 text-neutral-400">{user.created_at ? new Date(user.created_at).toLocaleDateString() : "-"}</td>
                    <td className="px-5 py-4">
                      <div className="flex justify-end gap-2">
                        <button className="icon-btn" onClick={() => editUser(user)} title="Editar"><Save size={16} /></button>
                        <button className="icon-btn danger" onClick={() => removeUser(user.id)} title="Eliminar"><Trash2 size={16} /></button>
                      </div>
                    </td>
                  </tr>
                ))}
                {filteredUsers.length === 0 && (
                  <tr>
                    <td className="px-5 py-10 text-center text-neutral-400" colSpan="6">No se encontraron usuarios con esos filtros.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
}

function CamerasPanel({ status, streamUrl }) {
  const [expandedCamera, setExpandedCamera] = useState(null);
  const alertState = status?.alert_status;
  const recentDetections = status?.recent_detections || [];
  const currentAlert = status?.current_alert;
  const cameras = Array.from({ length: 6 }).map((_, index) => ({
    id: index + 1,
    name: `Camara ${index + 1}`,
    location: index === 0 ? "Laptop local" : "Canal sin asignar",
    connected: index === 0 && Boolean(status?.camera_open),
    streamUrl: index === 0 ? streamUrl : null,
  }));
  const activeCamera = cameras.find((camera) => camera.id === expandedCamera);

  return (
    <div className="space-y-5">
      <section className="panel">
        <PanelHeader icon={Monitor} title="Matriz de camaras" aside={`${cameras.filter((camera) => camera.connected).length}/6 conectadas`} />
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {cameras.map((camera) => (
            <CameraTile key={camera.id} camera={camera} onExpand={() => setExpandedCamera(camera.id)} />
          ))}
        </div>
      </section>

      <section className="panel max-w-5xl">
        <PanelHeader icon={Activity} title="Estado tecnico" />
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <StatusLine label="Camara" value={status?.camera_open ? "Conectada" : "No disponible"} />
          <StatusLine label="Modelo YOLO" value={status?.model_loaded ? "Cargado" : "Pendiente"} />
          <StatusLine label="Detecciones actuales" value={String(status?.detections?.length || 0)} />
          <StatusLine label="Detecciones recientes" value={String(recentDetections.length)} />
        </div>
        <div className="mt-4 grid gap-4 lg:grid-cols-[1.2fr_.8fr]">
          <div className="rounded border border-neutral-800 bg-neutral-950 p-4">
            <p className="mb-3 text-sm font-semibold text-neutral-200">Motor de alertas</p>
            <div className="grid gap-3 sm:grid-cols-3">
              <StatusLine label="Estado" value={alertState?.state || "idle"} />
              <StatusLine label="Alerta actual" value={currentAlert ? currentAlert.level : "Sin alerta"} />
              <StatusLine label="Ultimo evento" value={alertState?.event_id || "Sin evento"} />
            </div>
            <p className="mt-3 text-sm text-neutral-400">{alertState?.message || "Esperando detecciones."}</p>
          </div>
          <div className="rounded border border-neutral-800 bg-neutral-950 p-4">
            <p className="mb-3 text-sm font-semibold text-neutral-200">Etiquetas recientes</p>
            <div className="flex flex-wrap gap-2">
              {recentDetections.length ? (
                recentDetections.map((item) => (
                  <Badge key={item.label} tone="neutral">{item.label} {(item.confidence * 100).toFixed(0)}%</Badge>
                ))
              ) : (
                <span className="text-sm text-neutral-500">Sin objetos recientes</span>
              )}
            </div>
          </div>
        </div>
      </section>

      {activeCamera && (
        <CameraFullscreen camera={activeCamera} onClose={() => setExpandedCamera(null)} />
      )}
    </div>
  );
}

function CameraTile({ camera, onExpand }) {
  return (
    <article className="overflow-hidden rounded border border-neutral-800 bg-neutral-950">
      <div className="relative bg-black">
        {camera.connected ? (
          <img src={camera.streamUrl} alt={camera.name} className="aspect-video w-full object-contain" />
        ) : (
          <div className="grid aspect-video place-items-center bg-[linear-gradient(135deg,#09090b,#171717)]">
            <div className="text-center">
              <Camera className="mx-auto mb-3 text-neutral-600" size={32} />
              <p className="text-sm font-medium text-neutral-400">Sin senal</p>
            </div>
          </div>
        )}
        <div className="absolute left-3 top-3 flex items-center gap-2 rounded bg-black/70 px-2 py-1 text-xs">
          <span className={`h-2 w-2 rounded-full ${camera.connected ? "bg-emerald-400" : "bg-neutral-600"}`} />
          {camera.connected ? "En vivo" : "Desconectada"}
        </div>
        <button
          className="absolute right-3 top-3 grid h-9 w-9 place-items-center rounded bg-black/70 text-neutral-100 transition hover:bg-emerald-400 hover:text-neutral-950 disabled:cursor-not-allowed disabled:opacity-50"
          onClick={onExpand}
          disabled={!camera.connected}
          title="Ver en pantalla grande"
        >
          <Maximize2 size={17} />
        </button>
      </div>
      <div className="flex items-center justify-between gap-3 p-3">
        <div>
          <h3 className="text-sm font-semibold">{camera.name}</h3>
          <p className="text-xs text-neutral-500">{camera.location}</p>
        </div>
        <Badge tone={camera.connected ? "emerald" : "neutral"}>{camera.connected ? "Activa" : "Libre"}</Badge>
      </div>
    </article>
  );
}

function CameraFullscreen({ camera, onClose }) {
  return (
    <div className="fixed inset-0 z-50 bg-black/90 p-4 backdrop-blur">
      <div className="mx-auto flex h-full max-w-7xl flex-col">
        <div className="mb-3 flex items-center justify-between gap-3 rounded border border-neutral-800 bg-neutral-950 px-4 py-3">
          <div>
            <h3 className="font-semibold">{camera.name}</h3>
            <p className="text-sm text-neutral-400">{camera.location} - transmision en vivo</p>
          </div>
          <button className="icon-btn" onClick={onClose} title="Cerrar pantalla grande">
            <X size={18} />
          </button>
        </div>
        <div className="grid min-h-0 flex-1 place-items-center overflow-hidden rounded border border-neutral-800 bg-black">
          <img src={camera.streamUrl} alt={camera.name} className="max-h-full max-w-full object-contain" />
        </div>
      </div>
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

function SettingsPanel({ whatsappStatus, testWhatsapp }) {
  const detectionOptions = [
    ["Deteccion de personas", "Activa el reconocimiento de presencia humana."],
    ["Arma de fuego", "Detecta armas de fuego entrenadas como arma_de_fuego."],
    ["Arma blanca", "Detecta cuchillos u objetos cortopunzantes como arma_blanca."],
    ["Rostro cubierto", "Detecta pasamontana, mascarilla y casco."],
  ];
  const systemOptions = [
    ["Grabacion automatica", "Desactivado mientras el sistema esta en modo solo deteccion.", false],
    ["Notificaciones push", "Preparado para activar alertas en tiempo real.", true],
    ["Guardar evidencias", "Guarda imagen y video en Supabase Storage cuando hay alerta amarilla o roja.", true],
    ["Modo laboratorio", "Permite pruebas de imagen/video sin afectar Supabase.", true],
  ];

  return (
    <div className="space-y-5">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Stat icon={Settings} label="Modo" value="Deteccion" tone="emerald" />
        <Stat icon={Shield} label="Storage" value="Supabase" tone="emerald" />
        <Stat icon={FlaskConical} label="Modelo" value="best.pt" tone="sky" />
        <Stat icon={Activity} label="Frame skip" value="3" tone="amber" />
      </section>

      <div className="grid gap-5 xl:grid-cols-[1fr_420px]">
        <section className="panel overflow-hidden p-0">
          <div className="border-b border-neutral-800 bg-neutral-950/70 p-5">
            <PanelHeader icon={Settings} title="Reglas de deteccion" aside="YOLO runtime" />
            <p className="text-sm text-neutral-400">Preferencias visuales para el comportamiento actual del sistema.</p>
          </div>
          <div className="grid gap-3 p-5 md:grid-cols-2">
            {detectionOptions.map(([title, detail]) => (
              <SettingToggle key={title} title={title} detail={detail} defaultChecked />
            ))}
          </div>
        </section>

        <section className="panel overflow-hidden p-0">
          <div className="border-b border-neutral-800 bg-neutral-950/70 p-5">
            <PanelHeader icon={Shield} title="Operacion" aside="Local" />
            <p className="text-sm text-neutral-400">Estado de almacenamiento y acciones automaticas.</p>
          </div>
          <div className="space-y-3 p-5">
            {systemOptions.map(([title, detail, enabled]) => (
              <SettingToggle key={title} title={title} detail={detail} defaultChecked={enabled} />
            ))}
          </div>
        </section>
      </div>

      <section className="panel">
        <PanelHeader icon={Activity} title="Parametros actuales" aside="Solo lectura" />
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <StatusLine label="Backend" value="http://127.0.0.1:8001" />
          <StatusLine label="Camara" value="Laptop local / indice 0" />
          <StatusLine label="Evidencias" value="Activas para alertas" />
          <StatusLine label="Supabase Storage" value="evidencias/alerta_roja y evidencias/alerta_amarilla" />
        </div>
      </section>

      <section className="panel">
        <PanelHeader icon={MessageCircle} title="WhatsApp Cloud API" aside={whatsappStatus?.enabled ? "Habilitado" : "Pendiente"} />
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <StatusLine label="Token" value={whatsappStatus?.has_token ? "Configurado" : "Falta token"} />
          <StatusLine label="Phone Number ID" value={whatsappStatus?.phone_number_id_valid ? whatsappStatus.phone_number_id : "Invalido"} />
          <StatusLine label="Version Graph" value={whatsappStatus?.graph_version || "-"} />
          <StatusLine label="Destinatarios" value={String(whatsappStatus?.recipients?.length || 0)} />
          <StatusLine label="Plantilla" value={whatsappStatus?.send_template_first ? `${whatsappStatus?.template_name || "-"} (${whatsappStatus?.template_language || "-"})` : "No usa plantilla"} />
          <StatusLine label="Variables plantilla" value={whatsappStatus?.template_body_params ? "Envia alerta en {{1}}" : "Sin variables"} />
        </div>
        <div className="mt-4 rounded border border-neutral-800 bg-neutral-950 p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-medium text-neutral-100">Prueba de envio</p>
              <p className="mt-1 text-xs text-neutral-500">Envia un mensaje al primer usuario activo con numero registrado.</p>
            </div>
            <button className="btn-muted" onClick={testWhatsapp}>
              <RefreshCw size={16} />
              Probar WhatsApp
            </button>
          </div>
          {whatsappStatus?.last_error && (
            <pre className="mt-4 max-h-40 overflow-auto rounded border border-red-900 bg-red-950/30 p-3 text-xs text-red-100">
              {JSON.stringify(whatsappStatus.last_error, null, 2)}
            </pre>
          )}
          <div className="mt-4 grid gap-2 md:grid-cols-2">
            {(whatsappStatus?.recipients || []).map((item) => (
              <StatusLine key={item.id} label={`${item.nombres || ""} ${item.apellidos || ""}`.trim() || "Usuario"} value={item.whatsapp || "Sin numero"} />
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

function SettingToggle({ title, detail, defaultChecked = true }) {
  return (
    <label className="flex items-start justify-between gap-4 rounded border border-neutral-800 bg-neutral-950 p-4">
      <span>
        <span className="block text-sm font-medium text-neutral-100">{title}</span>
        <span className="mt-1 block text-xs leading-5 text-neutral-500">{detail}</span>
      </span>
      <input className="mt-1" type="checkbox" defaultChecked={defaultChecked} />
    </label>
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
        <article key={event.id} className="overflow-hidden rounded border border-neutral-800 bg-neutral-950">
          {!compact && (event.imagen_evidencia_url || event.video_evidencia_url) && (
            <div className="grid gap-3 border-b border-neutral-800 bg-black/40 p-3 lg:grid-cols-2">
              {event.imagen_evidencia_url && (
                <a href={event.imagen_evidencia_url} target="_blank" rel="noreferrer" className="block overflow-hidden rounded border border-neutral-800 bg-black">
                  <img src={event.imagen_evidencia_url} alt={`Imagen del evento ${event.tipo_evento}`} className="aspect-video w-full object-contain" />
                </a>
              )}
              {event.video_evidencia_url && (
                <div className="overflow-hidden rounded border border-neutral-800 bg-black">
                  <video key={event.video_evidencia_url} className="aspect-video w-full object-contain" controls preload="metadata">
                    <source src={event.video_evidencia_url} type="video/mp4" />
                  </video>
                  <div className="flex items-center justify-between gap-2 border-t border-neutral-800 px-3 py-2 text-xs text-neutral-400">
                    <span>Video MP4</span>
                    <a className="text-emerald-300 hover:text-emerald-200" href={event.video_evidencia_url} target="_blank" rel="noreferrer">
                      Abrir video
                    </a>
                  </div>
                </div>
              )}
            </div>
          )}
          <div className="p-4">
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
            {!compact && (
              <div className="mt-3 grid gap-2 text-xs text-neutral-500 lg:grid-cols-2">
                <StatusLine label="URL imagen" value={event.imagen_evidencia_url || "Sin imagen"} />
                <StatusLine label="URL video" value={event.video_evidencia_url || "Sin video"} />
              </div>
            )}
          </div>
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
    sky: "border-sky-900 bg-sky-950/60 text-sky-200",
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
