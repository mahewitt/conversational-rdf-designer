"use client";

import { CopilotChat, UseAgentUpdate, useAgent, useInterrupt } from "@copilotkit/react-core/v2";
import { Background, Controls, Edge, Node, NodeChange, ReactFlow, applyNodeChanges } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

const initialNodes: Node[] = [];
const initialEdges: Edge[] = [];

type SharedGraphState = { nodes: Node[]; edges: Edge[]; rdf: string; namespace?: { prefix: string; namespace: string } };
type ClearGraphInterrupt = { title?: string; message?: string; reason?: string; request_reason?: string; details?: { entities?: number; relationships?: number }; metadata?: { langgraph?: { raw?: ClearGraphInterrupt } } };

function clearGraphInterrupt(value: unknown): ClearGraphInterrupt | undefined {
  const interrupt = value as ClearGraphInterrupt | undefined;
  const raw = interrupt?.metadata?.langgraph?.raw;
  if (raw?.reason === "clear_graph_confirmation") return raw;
  if (interrupt?.reason === "clear_graph_confirmation") return interrupt;
  return undefined;
}

export default function Home() {
  const { agent } = useAgent({ agentId: "vibegraph", updates: [UseAgentUpdate.OnStateChanged, UseAgentUpdate.OnRunStatusChanged] });
  const state = agent.state as SharedGraphState | undefined;
  const running = agent.isRunning;
  const nodes = state?.nodes ?? initialNodes;
  const edges = state?.edges ?? initialEdges;

  function onNodesChange(changes: NodeChange[]) {
    const current = (agent.state as SharedGraphState | undefined) ?? { nodes: initialNodes, edges: initialEdges, rdf: "" };
    agent.setState({ ...current, nodes: applyNodeChanges(changes, current.nodes) });
  }

  useInterrupt<ClearGraphInterrupt>({
    agentId: "vibegraph",
    enabled: ({ value }) => clearGraphInterrupt(value) !== undefined,
    render: ({ interrupt, event, resolve, cancel }) => {
      const value = clearGraphInterrupt(interrupt) ?? clearGraphInterrupt(event.value) ?? {};
      return <div className="hitl-card"><h3>{value.title ?? "Clear graph?"}</h3><p>{value.message ?? "This will delete all entities and relationships."}</p>{value.request_reason && <p className="hitl-reason">Reason: {value.request_reason}</p>}<div className="hitl-details"><span>{value.details?.entities ?? 0} entities</span><span>{value.details?.relationships ?? 0} relationships</span></div><div className="hitl-actions"><button className="danger" onClick={() => resolve({ approved: true })}>Clear graph</button><button onClick={() => cancel()}>Cancel</button></div></div>;
    },
  });

  return <main className="shell">
    <aside className="sidebar">
      <div className="brand-mark">V</div><div className="brand">VibeGraph <span>STUDIO</span></div>
      <div className="eyebrow">WORKSPACE</div><button className="nav active">◈ <span>Model canvas</span></button><button className="nav">▣ <span>Documents</span></button><button className="nav">⌘ <span>Saved models</span></button>
      <div className="sidebar-footer"><div className="status-dot" /> Local prototype<br /><small>Hour 1 workspace</small></div>
    </aside>
    <section className="workspace">
      <header><div><div className="eyebrow">SEMANTIC DESIGNER / UNTITLED MODEL</div><h1>Shape knowledge together.</h1></div><button className="export">Export RDF <span>↗</span></button></header>
      <div className="content"><section className="chat-panel"><div className="panel-heading"><span>Conversation</span><b>{running ? "STREAMING" : "LIVE"}</b></div><div className="copilot-chat"><CopilotChat agentId="vibegraph" labels={{ modalHeaderTitle: "VibeGraph Agent", welcomeMessageText: "Describe a domain and I'll sketch its semantic model." }} /></div></section>
        <section className="canvas-panel"><div className="canvas-toolbar"><span>MODEL CANVAS <b>{nodes.length} entities</b></span><span className="toolbar-actions">＋　−　⛶</span></div><div className="flow-wrap"><ReactFlow nodes={nodes} edges={edges} onNodesChange={onNodesChange} fitView><Background color="#d7e5e6" gap={22} size={1} /><Controls showInteractive={false} /></ReactFlow><div className="canvas-caption"><span className="legend teal" /> Class <span className="legend line" /> Object property</div></div></section>
        <aside className="rdf-panel"><div className="panel-heading"><span>RDF preview</span><span className="lock">LIVE STATE</span></div>{state?.rdf ? <pre className="rdf-output">{state.rdf}</pre> : <div className="rdf-placeholder"><div className="code-icon">{`</>`}</div><h2>Semantic output<br />will appear here</h2><p>As the graph evolves, VibeGraph will generate machine-readable Turtle.</p><div className="code-lines"><i /><i /><i /><i /></div></div>}</aside>
      </div>
    </section>
  </main>;
}
