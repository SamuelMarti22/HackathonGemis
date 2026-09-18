import { Routes, Route, Navigate } from "react-router-dom";
import Sidebar from "./components/Sidebar.jsx";
import AsistenteLegal from "./pages/AsistenteLegal.jsx";
import MisDocumentos from "./pages/MisDocumentos.jsx";
import BibliotecaNormativa from "./pages/BibliotecaNormativa.jsx";
import EditorDocumento from "./pages/EditorDocumento.jsx";

export default function App() {
  return (
    <div className="flex h-screen bg-slate-50">
      <Sidebar />
      <main className="flex flex-1 flex-col overflow-hidden">
        <Routes>
          <Route path="/" element={<Navigate to="/asistente-legal" replace />} />
          <Route path="/asistente-legal" element={<AsistenteLegal />} />
          <Route path="/documentos" element={<MisDocumentos />} />
          <Route path="/documentos/:id/editar" element={<EditorDocumento />} />
          <Route path="/biblioteca-normativa" element={<BibliotecaNormativa />} />
        </Routes>
      </main>
    </div>
  );
}
