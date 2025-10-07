"use client";

import { AssistantModal } from "@/components/assistant-ui/assistant-modal";
import { AssistantRuntimeProvider } from "@assistant-ui/react";
import { useChatRuntime } from "@assistant-ui/react-ai-sdk";

export default function Home() {
  const runtime = useChatRuntime({
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <div className="h-full">
        <AssistantModal />
      </div>
    </AssistantRuntimeProvider>
  );
}