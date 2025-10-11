'use client';

import { AssistantRuntimeProvider } from '@assistant-ui/react';
import { useDataStreamRuntime } from '@assistant-ui/react-data-stream';
import { AssistantModal } from '@/components/assistant-ui/assistant-modal';

export function MyAssistantModal() {
  const runtime = useDataStreamRuntime({
    api: '/api/chat',
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <AssistantModal />
    </AssistantRuntimeProvider>
  );
}
