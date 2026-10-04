import assert from 'node:assert/strict';
import { afterEach, test } from 'node:test';
import { streamChatMessage } from './chatService.js';

const originalFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = originalFetch;
});

test('streams sources and tokens when server events span network chunks', async () => {
  const encoder = new TextEncoder();
  const events = [];
  let request;
  globalThis.fetch = async (url, options) => {
    request = { url, options };
    const chunks = [
      'data: {"type":"sources","sources":[{"bread',
      'crumb":"SOP"}]}\n\ndata: {"type":"token","content":"Answer"}\n\n',
      'data: {"type":"error","message":"Provider warning"}\n'
    ];
    return new Response(new ReadableStream({
      start(controller) {
        for (const chunk of chunks) controller.enqueue(encoder.encode(chunk));
        controller.close();
      }
    }));
  };

  await streamChatMessage({
    query: 'How?',
    history: [{ role: 'user', content: 'Earlier' }],
    handlers: {
      onSources: (sources) => events.push(['sources', sources]),
      onToken: (content) => events.push(['token', content]),
      onError: (message) => events.push(['error', message])
    }
  });

  assert.equal(request.url, '/api/chat');
  assert.deepEqual(JSON.parse(request.options.body), {
    query: 'How?',
    history: [{ role: 'user', content: 'Earlier' }],
    top_k: 4
  });
  assert.deepEqual(events, [
    ['sources', [{ breadcrumb: 'SOP' }]],
    ['token', 'Answer'],
    ['error', 'Provider warning']
  ]);
});

test('reports API error details for unsuccessful chat requests', async () => {
  globalThis.fetch = async () => Response.json({ detail: 'Model unavailable' }, { status: 503 });

  await assert.rejects(
    streamChatMessage({
      query: 'How?',
      history: [],
      handlers: { onSources() {}, onToken() {}, onError() {} }
    }),
    /Model unavailable/
  );
});
