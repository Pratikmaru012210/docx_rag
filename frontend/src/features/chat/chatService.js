async function readRequestError(response) {
  try {
    const payload = await response.json();
    return payload.detail || `HTTP Error: ${response.status}`;
  } catch {
    return `HTTP Error: ${response.status}`;
  }
}

function processEventLine(line, handlers) {
  if (!line.startsWith('data: ')) return;

  const event = JSON.parse(line.slice(6));
  if (event.type === 'sources') {
    handlers.onSources(event.sources);
  } else if (event.type === 'token') {
    handlers.onToken(event.content);
  } else if (event.type === 'error') {
    handlers.onError(event.message);
  }
}

export async function streamChatMessage({ query, history, handlers, signal }) {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, history, top_k: 4 }),
    signal
  });

  if (!response.ok) {
    throw new Error(await readRequestError(response));
  }
  if (!response.body) {
    throw new Error('The server did not provide a chat response stream.');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let pending = '';

  while (true) {
    const { value, done } = await reader.read();
    pending += decoder.decode(value, { stream: !done });

    const lines = pending.split('\n');
    pending = lines.pop() || '';
    for (const line of lines) {
      processEventLine(line, handlers);
    }

    if (done) break;
  }

  if (pending) processEventLine(pending, handlers);
}
