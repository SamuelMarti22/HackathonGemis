// Datos de ejemplo (mock) para "Biblioteca normativa", que todavía no tiene
// endpoint en el backend. El chat y "Mis documentos" ya consumen el backend
// real (ver src/api/chat.js y src/api/documents.js).

export const mockNormas = [
  {
    id: "n-1",
    titulo: "Constitución Política de Colombia",
    categoria: "Constitucional",
    descripcion: "Carta fundamental que consagra los derechos y deberes de los colombianos.",
    url: "https://www.constitucioncolombia.com/",
  },
  {
    id: "n-2",
    titulo: "Ley Estatutaria 1751 de 2015",
    categoria: "Salud",
    descripcion: "Regula el derecho fundamental a la salud.",
    url: "https://www.minsalud.gov.co/Normatividad_Nuevo/Ley%201751%20de%202015.pdf",
  },
  {
    id: "n-3",
    titulo: "Decreto 2591 de 1991",
    categoria: "Tutela",
    descripcion: "Reglamenta la acción de tutela consagrada en el artículo 86 de la Constitución.",
    url: "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=4114",
  },
  {
    id: "n-4",
    titulo: "Código Sustantivo del Trabajo",
    categoria: "Laboral",
    descripcion: "Regula las relaciones laborales individuales entre trabajadores y empleadores.",
    url: "https://www.mintrabajo.gov.co/documents/20147/0/Codigo+Sustantivo+del+Trabajo.pdf",
  },
];
