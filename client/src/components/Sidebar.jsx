import { NavLink } from "react-router-dom";

const linkBase =
  "flex items-center gap-3 rounded-xl px-4 py-3 text-slate-600 hover:bg-slate-100 transition-colors";
const linkActive = "bg-blue-50 text-blue-700 font-semibold hover:bg-blue-50";

export default function Sidebar() {
  return (
    <aside className="flex h-screen w-72 flex-col border-r border-slate-200 bg-white px-4 py-6">
      <div className="mb-6 flex items-center gap-3 px-2">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-50 text-xl">
          ⚖️
        </div>
        <div>
          <p className="font-bold text-slate-900 leading-none">Lexi</p>
          <p className="text-xs text-slate-500">Asistente constitucional</p>
        </div>
      </div>

      <NavLink
        to="/asistente-legal"
        end
        className="mb-6 flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-3 font-semibold text-white shadow-sm hover:bg-blue-700 transition-colors"
      >
        <span className="text-lg leading-none">+</span> Nuevo caso
      </NavLink>

      <nav className="flex flex-col gap-1">
        <NavLink
          to="/asistente-legal"
          className={({ isActive }) => `${linkBase} ${isActive ? linkActive : ""}`}
        >
          <span>💬</span> Asistente legal
        </NavLink>
        <NavLink
          to="/documentos"
          className={({ isActive }) => `${linkBase} ${isActive ? linkActive : ""}`}
        >
          <span>📄</span> Mis documentos
        </NavLink>
        <NavLink
          to="/biblioteca-normativa"
          className={({ isActive }) => `${linkBase} ${isActive ? linkActive : ""}`}
        >
          <span>📖</span> Biblioteca normativa
        </NavLink>
      </nav>
    </aside>
  );
}
