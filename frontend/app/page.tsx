"use client";

import { CopilotChat, UseAgentUpdate, useAgent, useInterrupt, useRenderTool } from "@copilotkit/react-core/v2";
import { Background, Controls, Edge, Node, NodeChange, ReactFlow, applyNodeChanges } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useRef } from "react";

const initialNodes: Node[] = [];
const initialEdges: Edge[] = [];

type SharedGraphState = {
  nodes: Node[];
  edges: Edge[];
  rdf: string;
  speckit?: string;
  namespace?: { prefix: string; namespace: string };
};
type ClearGraphInterrupt = {
  title?: string;
  message?: string;
  reason?: string;
  request_reason?: string;
  details?: { entities?: number; relationships?: number };
  metadata?: { langgraph?: { raw?: ClearGraphInterrupt } };
};

function clearGraphInterrupt(value: unknown): ClearGraphInterrupt | undefined {
  const interrupt = value as ClearGraphInterrupt | undefined;
  const raw = interrupt?.metadata?.langgraph?.raw;
  if (raw?.reason === "clear_graph_confirmation") return raw;
  if (interrupt?.reason === "clear_graph_confirmation") return interrupt;
  return undefined;
}

function triggerDownload(
  content: string,
  filename: string,
  mimeType = "text/turtle;charset=utf-8",
  defaultExtension = ".ttl",
) {
  if (!content) return;
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  let name = filename || `model${defaultExtension}`;
  if (!name.endsWith(defaultExtension)) name = `${name}${defaultExtension}`;
  link.download = name;
  document.body.appendChild(link);
  link.click();
  setTimeout(() => {
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, 1000);
}

export default function Home() {
  const { agent } = useAgent({
    agentId: "vibegraph",
    updates: [UseAgentUpdate.OnStateChanged, UseAgentUpdate.OnRunStatusChanged],
  });
  const state = agent.state as SharedGraphState | undefined;
  const running = agent.isRunning;
  const nodes = state?.nodes ?? initialNodes;
  const edges = state?.edges ?? initialEdges;

  const latestStateRef = useRef<SharedGraphState | undefined>(state);
  latestStateRef.current = state;

  const downloadedCallsRef = useRef<Set<string>>(new Set());

  function onNodesChange(changes: NodeChange[]) {
    const current = (agent.state as SharedGraphState | undefined) ?? {
      nodes: initialNodes,
      edges: initialEdges,
      rdf: "",
    };
    agent.setState({ ...current, nodes: applyNodeChanges(changes, current.nodes) });
  }

  function handleExportRDF(customFilename?: string) {
    const content = latestStateRef.current?.rdf;
    if (!content) return;
    triggerDownload(content, customFilename || "model.ttl", "text/turtle;charset=utf-8", ".ttl");
  }

  function handleExportSpecKit(customFilename?: string) {
    const content = latestStateRef.current?.speckit;
    if (!content) return;
    triggerDownload(content, customFilename || "spec.md", "text/markdown;charset=utf-8", ".md");
  }

  useRenderTool({
    name: "*",
    agentId: "vibegraph",
    render: (props) => {
      if (props.name !== "save_model" && props.name !== "save_speckit") return <></>;

      if (props.status === "complete" && props.toolCallId && !downloadedCallsRef.current.has(props.toolCallId)) {
        downloadedCallsRef.current.add(props.toolCallId);

        let parsedResult: any = {};
        if (typeof props.result === "string") {
          try {
            parsedResult = JSON.parse(props.result);
          } catch {
            parsedResult = { message: props.result };
          }
        } else if (props.result && typeof props.result === "object") {
          parsedResult = props.result;
        }

        const params = (props as any).parameters || (props as any).args || {};
        const isSpeckit = props.name === "save_speckit";
        const filename = parsedResult.filename || params.name || (isSpeckit ? "spec.md" : "model.ttl");

        setTimeout(() => {
          if (isSpeckit) {
            const content = latestStateRef.current?.speckit;
            if (content) triggerDownload(content, filename, "text/markdown;charset=utf-8", ".md");
          } else {
            const content = latestStateRef.current?.rdf;
            if (content) triggerDownload(content, filename, "text/turtle;charset=utf-8", ".ttl");
          }
        }, 100);
      }

      return <></>;
    },
  });

  useInterrupt<ClearGraphInterrupt>({
    agentId: "vibegraph",
    enabled: ({ value }) => clearGraphInterrupt(value) !== undefined,
    render: ({ interrupt, event, resolve, cancel }) => {
      const value = clearGraphInterrupt(interrupt) ?? clearGraphInterrupt(event.value) ?? {};
      return (
        <div className="hitl-card">
          <h3>{value.title ?? "Clear graph?"}</h3>
          <p>{value.message ?? "This will delete all entities and relationships."}</p>
          {value.request_reason && <p className="hitl-reason">Reason: {value.request_reason}</p>}
          <div className="hitl-details">
            <span>{value.details?.entities ?? 0} entities</span>
            <span>{value.details?.relationships ?? 0} relationships</span>
          </div>
          <div className="hitl-actions">
            <button
              className="danger"
              onClick={() => resolve({ approved: true })}
            >
              Clear graph
            </button>
            <button onClick={() => cancel()}>Cancel</button>
          </div>
        </div>
      );
    },
  });

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand-mark">V</div>
        <div className="brand">
          VibeGraph <span>STUDIO</span>
        </div>
        <div className="eyebrow">WORKSPACE</div>
        <button className="nav active">
          ◈ <span>Model canvas</span>
        </button>
        <button className="nav">
          ▣ <span>Documents</span>
        </button>
        <button className="nav">
          ⌘ <span>Saved models</span>
        </button>
        <div className="sidebar-footer">
          <div className="status-dot" /> Local prototype
          <br />
          <small>Hour 1 workspace</small>
        </div>
      </aside>
      <section className="workspace">
        <header>
          <div>
            <div className="eyebrow">SEMANTIC DESIGNER / UNTITLED MODEL</div>
            <h1>Shape knowledge together.</h1>
          </div>
          <div className="header-actions">
            <button
              className="export"
              onClick={() => handleExportRDF()}
              disabled={!state?.rdf}
            >
              Export RDF <span>↗</span>
            </button>
            <button
              className="export"
              onClick={() => handleExportSpecKit()}
              disabled={!state?.speckit}
            >
              Save Spec-Kit <span>↗</span>
            </button>
          </div>
        </header>
        <div className="content">
          <section className="chat-panel">
            <div className="panel-heading">
              <span>Conversation</span>
              <b>{running ? "STREAMING" : "LIVE"}</b>
            </div>
            <div className="copilot-chat">
              <CopilotChat
                agentId="vibegraph"
                attachments={{
                  enabled: true,
                  accept: "image/*,.png,.jpg,.jpeg,.webp,.gif,.pdf",
                  maxSize: 10 * 1024 * 1024,
                }}
                labels={{
                  modalHeaderTitle: "VibeGraph Agent",
                  welcomeMessageText:
                    "Describe a domain or drop an ER diagram image and I'll sketch its semantic model.",
                }}
              />
            </div>
          </section>
          <section className="canvas-panel">
            <div className="canvas-toolbar">
              <span>
                MODEL CANVAS <b>{nodes.length} entities</b>
              </span>
              <span className="toolbar-actions">＋　−　⛶</span>
            </div>
            <div className="flow-wrap">
              <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                fitView
              >
                <Background
                  color="#d7e5e6"
                  gap={22}
                  size={1}
                />
                <Controls showInteractive={false} />
              </ReactFlow>
              <div className="canvas-caption">
                <span className="legend teal" /> Class <span className="legend line" /> Object property
              </div>
            </div>
          </section>
          <aside className="rdf-panel">
            <div className="panel-heading">
              <span>RDF preview</span>
              <span className="lock">LIVE STATE</span>
            </div>
            {state?.rdf ? (
              <pre className="rdf-output">{state.rdf}</pre>
            ) : (
              <div className="rdf-placeholder">
                <div className="code-icon">{`</>`}</div>
                <h2>
                  Semantic output
                  <br />
                  will appear here
                </h2>
                <p>As the graph evolves, VibeGraph will generate machine-readable Turtle.</p>
                <div className="code-lines">
                  <i />
                  <i />
                  <i />
                  <i />
                </div>
              </div>
            )}
          </aside>
        </div>
      </section>
    </main>
  );
}
