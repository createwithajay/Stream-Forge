import React, { useCallback, useEffect, useRef, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  MarkerType,
  Position,
  useEdgesState,
  useNodesState,
} from "reactflow";
import "reactflow/dist/style.css";
import "./forge.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

// ---- Layout: fixed left-to-right pipeline positions ----
const LAYOUT = {
  kafka: { x: 40, y: 160 },
  faust: { x: 340, y: 160 },
  rocksdb: { x: 640, y: 160 },
  chaos: { x: 940, y: 160 },
};

function heatFor(node) {
  // 0 = cool/idle, 1 = full ember (bottlenecked)
  if (!node) return 0;
  if (node.bottleneck) return 1;
  const t = Math.min(1, node.throughput_eps / 8000);
  return t * 0.55; // healthy flow glows warm-teal, not red
}

function ForgeNode({ data }) {
  const heat = heatFor(data.metrics);
  const hot = data.metrics?.bottleneck;
  const bg = hot
    ? `linear-gradient(135deg, #3a1408, #5c1d0a)`
    : `linear-gradient(135deg, #14181d, #1c2229)`;
  const glow = hot
    ? "0 0 22px rgba(255,107,53,0.55), 0 0 2px rgba(255,107,53,0.9)"
    : `0 0 ${8 + heat * 14}px rgba(94,234,212,${0.15 + heat * 0.25})`;
  const border = hot ? "#ff6b35" : `rgba(94,234,212,${0.25 + heat * 0.5})`;

  return (
    <div
      className="forge-node"
      style={{ background: bg, boxShadow: glow, borderColor: border }}
    >
      <div className="forge-node-role">{data.role}</div>
      <div className="forge-node-label">{data.label}</div>
      {data.metrics ? (
        <div className="forge-node-stats">
          <span>{data.metrics.throughput_eps.toLocaleString()} ev/s</span>
          <span className={hot ? "stat-hot" : ""}>
            {data.metrics.latency_ms} ms
          </span>
        </div>
      ) : (
        <div className="forge-node-stats stat-dim">connecting…</div>
      )}
      {hot && <div className="forge-node-flag">BOTTLENECK</div>}
    </div>
  );
}

const nodeTypes = { forge: ForgeNode };

export default function App() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [connected, setConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  const esRef = useRef(null);

  const applySnapshot = useCallback(
    (snapshot) => {
      const metricsById = Object.fromEntries(
        snapshot.nodes.map((n) => [n.id, n])
      );

      setNodes(
        snapshot.nodes.map((n) => ({
          id: n.id,
          type: "forge",
          position: LAYOUT[n.id] || { x: 0, y: 0 },
          data: { label: n.label, role: n.role, metrics: n },
          sourcePosition: Position.Right,
          targetPosition: Position.Left,
        }))
      );

      setEdges(
        snapshot.edges.map((e) => {
          const hot = metricsById[e.source]?.bottleneck;
          return {
            id: e.id,
            source: e.source,
            target: e.target,
            animated: true,
            style: {
              stroke: hot ? "#ff6b35" : "#3a4552",
              strokeWidth: hot ? 3 : 2,
            },
            markerEnd: {
              type: MarkerType.ArrowClosed,
              color: hot ? "#ff6b35" : "#5b6b7d",
            },
          };
        })
      );
      setLastUpdate(new Date());
    },
    [setNodes, setEdges]
  );

  useEffect(() => {
    // Try live SSE stream first; fall back to polling if it fails.
    let poll;
    fetch(`${API_BASE}/health`)
      .then(() => {
        setConnected(true);
        const es = new EventSource(`${API_BASE}/api/stream`);
        esRef.current = es;
        es.onmessage = (evt) => applySnapshot(JSON.parse(evt.data));
        es.onerror = () => {
          es.close();
          setConnected(false);
          poll = setInterval(() => {
            fetch(`${API_BASE}/api/topology`)
              .then((r) => r.json())
              .then(applySnapshot)
              .then(() => setConnected(true))
              .catch(() => setConnected(false));
          }, 2000);
        };
      })
      .catch(() => setConnected(false));

    return () => {
      esRef.current?.close();
      if (poll) clearInterval(poll);
    };
  }, [applySnapshot]);

  return (
    <div className="forge-app">
      <header className="forge-header">
        <div>
          <h1>Stream-Forge</h1>
          <p>Live pipeline topology · Role 5</p>
        </div>
        <div className={`forge-status ${connected ? "on" : "off"}`}>
          <span className="dot" />
          {connected ? "live" : "reconnecting…"}
          {lastUpdate && (
            <span className="forge-ts">
              {" "}
              · updated {lastUpdate.toLocaleTimeString()}
            </span>
          )}
        </div>
      </header>

      <div className="forge-canvas">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          fitView
          proOptions={{ hideAttribution: true }}
        >
          <Background color="#22282f" gap={22} />
          <Controls />
        </ReactFlow>
      </div>
    </div>
  );
}
