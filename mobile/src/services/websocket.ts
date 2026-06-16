const WS_BASE = "ws://localhost:8000";

export function connectTaskStream(
  taskId: string,
  onMessage: (data: any) => void,
  onClose: () => void
): WebSocket {
  const ws = new WebSocket(`${WS_BASE}/analysis/tasks/${taskId}/stream`);
  ws.onmessage = (event) => {
    try { onMessage(JSON.parse(event.data)); } catch (e) { /* ignore */ }
  };
  ws.onclose = onClose;
  ws.onerror = onClose;
  return ws;
}
