import assert from 'node:assert';
import { before, after, describe, it } from 'node:test';
import { server } from '../index.js';

let baseUrl;
let testServer;

describe('API validation', () => {
  before(() => {
    testServer = server.listen(0);
    const address = testServer.address();
    if (typeof address === 'object' && address) {
      baseUrl = `http://127.0.0.1:${address.port}`;
    }
  });

  after(async () => {
    await new Promise((resolve) => testServer.close(resolve));
  });

  it('rejects TTS requests without text', async () => {
    const response = await fetch(`${baseUrl}/api/tts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ voice: 'test-voice' }),
    });

    assert.strictEqual(response.status, 400);
    const body = await response.json();
    assert.match(body.error, /text/i);
  });

  it('rejects video requests without text', async () => {
    const response = await fetch(`${baseUrl}/api/video`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ voice: 'test-voice' }),
    });

    assert.strictEqual(response.status, 400);
    const body = await response.json();
    assert.match(body.error, /text/i);
  });

  it('returns 400 for non-numeric user id', async () => {
    const response = await fetch(`${baseUrl}/api/users/not-a-number`);
    assert.strictEqual(response.status, 400);
    const body = await response.json();
    assert.match(body.message, /positive integer/i);
  });
});
