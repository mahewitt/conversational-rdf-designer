"use client";

import { useState } from "react";
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

type AgentEvent = { type: string; data: { content?: string; graph?: { nodes: Node[]; edges: Edge[] } } };

export default function Home() {
  const [nodes, setNodes] = useState<Node[]>(initialNodes);
  const [edges, setEdges] = useState<Edge[]>(initialEdges);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState(["Describe a domain and I’ll sketch its semantic model."]);
  const [running, setRunning] = useState(false);

  async function sendMessage() {
    if (!message.trim() || running) return;
    const prompt = message.trim();
    setMessage("");
    setMessages((current) => [...current, prompt]);
    setRunning(true);
    const response = await fetch("http://localhost:8000/api/agent/stream", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message: prompt }),
    });
    const reader = response.body?.getReader();
    if (!reader) return;
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const chunks = buffer.split("\n\n");
      buffer = chunks.pop() ?? "";
      chunks.forEach((chunk) => {
        const type = chunk.match(/^event: (.+)$/m)?.[1];
        const raw = chunk.match(/^data: (.+)$/m)?.[1];
        if (!type || !raw) return;
        const agentEvent = { type, data: JSON.parse(raw) } as AgentEvent;
        if (agentEvent.type === "state_update" && agentEvent.data.graph) {
          setNodes(agentEvent.data.graph.nodes);
          setEdges(agentEvent.data.graph.edges);
        }
        if (agentEvent.type === "assistant_message" && agentEvent.data.content) setMessages((current) => [...current, agentEvent.data.content!]);
      });
    }
    setRunning(false);
  }

  return <main className="shell">
    <aside className="sidebar">
      <div className="brand-mark">V</div><div className="brand">VibeGraph <span>STUDIO</span></div>
      <div className="eyebrow">WORKSPACE</div><button className="nav active">◈ <span>Model canvas</span></button><button className="nav">▣ <span>Documents</span></button><button className="nav">⌘ <span>Saved models</span></button>
      <div className="sidebar-footer"><div className="status-dot" /> Local prototype<br /><small>Hour 1 workspace</small></div>
    </aside>
    <section className="workspace">
      <header><div><div className="eyebrow">SEMANTIC DESIGNER / UNTITLED MODEL</div><h1>Shape knowledge together.</h1></div><button className="export">Export RDF <span>↗</span></button></header>
      <div className="content"><section className="chat-panel"><div className="panel-heading"><span>Conversation</span><b>LIVE</b></div><div className="messages">{messages.map((item, index) => <div className={index % 2 ? "bubble user" : "bubble assistant"} key={`${item}-${index}`}>{item}</div>)}{running && <div className="typing">Agent is thinking <i /> <i /> <i /></div>}</div><div className="composer"><textarea value={message} onChange={(event) => setMessage(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); sendMessage(); } }} placeholder="Try: Create a facility with wells" /><button onClick={sendMessage} aria-label="Send message">↑</button><div className="composer-meta">⌘ Enter to send · semantic actions stream to canvas</div></div></section>
        <section className="canvas-panel"><div className="canvas-toolbar"><span>MODEL CANVAS <b>{nodes.length} entities</b></span><span className="toolbar-actions">＋　−　⛶</span></div><div className="flow-wrap"><ReactFlow nodes={nodes} edges={edges} fitView><Background color="#d7e5e6" gap={22} size={1} /><Controls showInteractive={false} /></ReactFlow><div className="canvas-caption"><span className="legend teal" /> Entity <span className="legend coral" /> Measurement <span className="legend line" /> Relationship</div></div></section>
        <aside className="rdf-panel"><div className="panel-heading"><span>RDF preview</span><span className="lock">HOUR 5</span></div><div className="rdf-placeholder"><div className="code-icon">{`</>`}</div><h2>Semantic output<br />will appear here</h2><p>As the graph evolves, VibeGraph will generate machine-readable Turtle.</p><div className="code-lines"><i /><i /><i /><i /></div></div></aside>
      </div>
    </section>
  </main>;
}
