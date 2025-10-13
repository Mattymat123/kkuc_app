import { type Message } from 'ai';

export const maxDuration = 60;

export async function POST(req: Request) {
  const body = await req.json();
  const { messages }: { messages: Message[] } = body;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 55000);

    // Simply proxy to the backend /chat endpoint
    // The backend handles thread management internally
    const response = await fetch(
      'http://0.0.0.0:8000/chat',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ messages }),
        signal: controller.signal,
      }
    );

    clearTimeout(timeoutId);

    if (!response.ok) {
      console.error(`[ERROR] Server responded with status ${response.status}`);
      const errorText = await response.text();
      console.error(`[ERROR] Response body: ${errorText}`);
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    if (!response.body) {
      console.error('[ERROR] No response body received');
      throw new Error('No response body received');
    }

    console.log('[DEBUG] Streaming response from backend...');
    
    // Return the stream directly
    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'X-Vercel-AI-Data-Stream': 'v1',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
  } catch (error) {
    console.error('[ERROR] Failed to process request:', error);
    
    return new Response(
      JSON.stringify({ error: 'Failed to process request', details: String(error) }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
}
