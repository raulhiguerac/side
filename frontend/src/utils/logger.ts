// Punto único de logs de error: acá se conecta el reporte remoto cuando exista.
export const logger = {
  error: (message: string, error?: unknown) => console.error(message, error),
};
