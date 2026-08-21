"use client";

import { CopilotKit } from "@copilotkit/react-core/v2";
import "@copilotkit/react-ui/styles.css";

export function CopilotKitProvider({ children }: Readonly<{ children: React.ReactNode }>) {
  return <CopilotKit runtimeUrl="/api/copilotkit" agent="vibegraph">{children}</CopilotKit>;
}
