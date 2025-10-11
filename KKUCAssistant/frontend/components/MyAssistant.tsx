'use client';

// import { useEdgeRuntime } from "@assistant-ui/react";
import { useChat } from 'ai/react';
import { Thread } from '@assistant-ui/react';
import { useVercelUseChatRuntime } from '@assistant-ui/react-ai-sdk';
import { MarkdownText } from '@/components/assistant-ui/markdown-text';
import { GetStockPriceToolUI } from './GetStockPriceToolUI';
import { ToolFallback } from './ToolFallBack';

export function MyAssistant() {
  // const runtime = useEdgeRuntime({ api: "/api/chat" });
  const chat = useChat({
    api: '/api/chat',
  });

  const runtime = useVercelUseChatRuntime(chat);

  return (
    <Thread
      runtime={runtime}
      assistantMessage={{ components: { Text: MarkdownText, ToolFallback } }}
      tools={[GetStockPriceToolUI]}
    />
  );
}
