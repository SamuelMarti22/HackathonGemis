// Datos de ejemplo (mock) para las secciones que aún no tienen endpoint en
// el backend: generación de documentos y biblioteca normativa. El chat
// ("Asistente legal") ya consume el backend real (ver src/api/chat.js).

export const mockDocumentos = [
  {
    id: "doc-1",
    titulo: "Derecho de petición a EPS",
    tipo: "Derecho de petición",
    estado: "Listo para revisar",
    editado: "Editado recientemente",
  },
  {
    id: "doc-2",
    titulo: "Solicitud de historia clínica",
    tipo: "Derecho de petición",
    estado: "Borrador",
    editado: "Editado recientemente",
  },
  {
    id: "doc-3",
    titulo: "Tutela por servicio de salud",
    tipo: "Acción de tutela",
    estado: "Listo para revisar",
    editado: "Editado recientemente",
  },
];

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

export const mockDocumentoContenido = {
  "doc-1": `Señores\nEPS XYZ\nCiudad\n\nAsunto: Derecho de petición - Autorización de procedimiento médico\n\nYo, [Nombre completo], identificado con C.C. No. [Número], radico la presente solicitud...`,
  "doc-2": `Señores\nHospital / Clínica\nCiudad\n\nAsunto: Solicitud de copia de historia clínica\n\nYo, [Nombre completo], identificado con C.C. No. [Número], solicito...`,
  "doc-3": `Señor(a) Juez\nReparto\nCiudad\n\nAccionante: [Nombre completo]\nAccionado: EPS XYZ\n\nAsunto: Acción de tutela por vulneración del derecho a la salud...`,
};
