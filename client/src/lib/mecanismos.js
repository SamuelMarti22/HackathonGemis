// Nombres legibles para los `tipo` que devuelve el backend (ver
// server/app/schemas.py -> MECANISMOS). Mismas claves, en snake_case.
export const MECANISMO_LABELS = {
  tutela: "Acción de tutela",
  derecho_de_peticion: "Derecho de petición",
  accion_de_cumplimiento: "Acción de cumplimiento",
  accion_popular: "Acción popular",
  habeas_corpus: "Habeas corpus",
  habeas_data: "Habeas data",
};

export function mecanismoNombre(tipo) {
  return MECANISMO_LABELS[tipo] ?? tipo;
}
