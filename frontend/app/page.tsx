"use client";

import { useCoAgent } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import { Background, Controls, Edge, Node, ReactFlow } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

const initialNodes: Node[] = [
  { id: "facility", position: { x: 100, y: 90 }, data: { label: "Facility", kind: "entity" }, type: "default" },
  { id: "well", position: { x: 390, y: 230 }, data: { label: "Well", kind: "entity" }, type: "default" },
  { id: "measurement", position: { x: 680, y: 90 }, data: { label: "Production Measurement", kind: "measurement" }, type: "default" },
];
const initialEdges: Edge[] = [
  { id: "facility-contains-well", source: "facility", target: "well", label: "contains", animated: true },
  { id: "well-produces-measurement", source: "well", target: "measurement", label: "produces" },
];

type SharedGraphState = { nodes: Node[]; edges: Edge[]; rdf: string };

export default function Home() {
  const { state, running } = useCoAgent<SharedGraphState>({ name: "vibegraph", initialState: { nodes: initialNodes, edges: initialEdges, rdf: "" } });
  const nodes = state?.nodes ?? initialNodes;
  const edges = state?.edges ?? initialEdges;

  return <main className="shell">
    <aside className="sidebar">
      <div className="brand-mark">V</div><div className="brand">VibeGraph <span>STUDIO</span></div>
      <div className="eyebrow">WORKSPACE</div><button className="nav active">◈ <span>Model canvas</span></button><button className="nav">▣ <span>Documents</span></button><button className="nav">⌘ <span>Saved models</span></button>
      <div className="sidebar-footer"><div className="status-dot" /> Local prototype<br /><small>Hour 1 workspace</small></div>
    </aside>
    <section className="workspace">
      <header><div><div className="eyebrow">SEMANTIC DESIGNER / UNTITLED MODEL</div><h1>Shape knowledge together.</h1></div><button className="export">Export RDF <span>↗</span></button></header>
      <div className="content"><section className="chat-panel"><div className="panel-heading"><span>Conversation</span><b>{running ? "STREAMING" : "LIVE"}</b></div><div className="copilot-chat"><CopilotChat instructions="You are VibeGraph, a semantic modelling assistant. Update the shared graph state from the user's modelling instructions." labels={{ title: "VibeGraph Agent", initial: "Describe a domain and I’ll sketch its semantic model." }} /></div></section>
        <section className="canvas-panel"><div className="canvas-toolbar"><span>MODEL CANVAS <b>{nodes.length} entities</b></span><span className="toolbar-actions">＋　−　⛶</span></div><div className="flow-wrap"><ReactFlow nodes={nodes} edges={edges} fitView><Background color="#d7e5e6" gap={22} size={1} /><Controls showInteractive={false} /></ReactFlow><div className="canvas-caption"><span className="legend teal" /> Entity <span className="legend coral" /> Measurement <span className="legend line" /> Relationship</div></div></section>
        <aside className="rdf-panel"><div className="panel-heading"><span>RDF preview</span><span className="lock">LIVE STATE</span></div>{state?.rdf ? <pre className="rdf-output">{state.rdf}</pre> : <div className="rdf-placeholder"><div className="code-icon">{`</>`}</div><h2>Semantic output<br />will appear here</h2><p>As the graph evolves, VibeGraph will generate machine-readable Turtle.</p><div className="code-lines"><i /><i /><i /><i /></div></div>}</aside>
      </div>
    </section>
  </main>;
}
