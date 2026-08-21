import { HttpAgent } from "@ag-ui/client";
import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";

const runtime = new CopilotRuntime({
  agents: {
    vibegraph: new HttpAgent({
      url: process.env.VIBEGRAPH_AGENT_URL ?? "http://localhost:8000/api/agent",
      agentId: "vibegraph",
    }),
  },
});

const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
  runtime,
  serviceAdapter: new ExperimentalEmptyAdapter(),
  endpoint: "/api/copilotkit",
});

export const POST = handleRequest;
