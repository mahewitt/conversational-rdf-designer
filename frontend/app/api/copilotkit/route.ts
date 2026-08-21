import { HttpAgent } from "@ag-ui/client";
import { CopilotRuntime, createCopilotRuntimeHandler } from "@copilotkit/runtime/v2";

const runtime = new CopilotRuntime({
  agents: {
    vibegraph: new HttpAgent({
      url: process.env.VIBEGRAPH_AGENT_URL ?? "http://localhost:8000/api/agent",
      agentId: "vibegraph",
    }),
  },
});

const handleRequest = createCopilotRuntimeHandler({
  runtime,
  basePath: "/api/copilotkit",
  mode: "single-route",
});

export const POST = handleRequest;
