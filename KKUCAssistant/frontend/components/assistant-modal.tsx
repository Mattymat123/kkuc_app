'use client';

import { useChat } from 'ai/react';
import { AssistantModal } from '@assistant-ui/react';
import { makeMarkdownText } from '@assistant-ui/react-markdown';
import { useVercelUseChatRuntime } from '@assistant-ui/react-ai-sdk';
import { GetStockPriceToolUI } from './GetStockPriceToolUI';
import { ToolFallback } from './ToolFallBack';

const MarkdownText = makeMarkdownText();

export function MyAssistantModal() {
  const chat = useChat({
    api: '/api/chat',
  });

  const runtime = useVercelUseChatRuntime(chat);

  return (
    <AssistantModal
      runtime={runtime}
      assistantMessage={{ components: { Text: MarkdownText, ToolFallback } }}
      tools={[GetStockPriceToolUI]}
    />
  );
}
