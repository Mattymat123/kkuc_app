'use client';

import { AssistantRuntimeProvider } from '@assistant-ui/react';
import { useDataStreamRuntime } from '@assistant-ui/react-data-stream';
import { Thread } from '@/components/assistant-ui/thread';

export function MyAssistant() {
  const runtime = useDataStreamRuntime({
    api: '/api/chat',
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <Thread />
    </AssistantRuntimeProvider>
  );
}
