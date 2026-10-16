import { useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  Handle,
  Position,
  MarkerType,
} from "@xyflow/react";
import type { NodeProps, Node } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { Preview, Topology } from "../types";
type Data = {
  name: string;
  depth: number;
  root: boolean;
  selected: boolean;
  owner: string;
};
function ServiceNode({ data }: NodeProps<Node<Data>>) {
  return (
    <div
      className={
        "service-node " +
        (data.root ? "root-node " : "") +
        (data.selected ? "selected-node" : "")
      }
    >
      <Handle type="target" position={Position.Right} />
      <span className="node-eyebrow">
        {data.root
          ? "CHANGE ROOT"
          : "SERVICE / " + String(data.depth).padStart(2, "0")}
      </span>
      <strong>{data.name}</strong>
      <span className="node-foot">
        {data.owner === "unowned"
          ? "Owner unassigned"
          : data.owner === "conflict"
            ? "Conflicting owners"
            : data.root
              ? "Proposed change"
              : "Source verified"}
        {(data.owner === "unowned" || data.owner === "conflict") && (
          <i className="amber-dot" />
        )}
      </span>
      <Handle type="source" position={Position.Left} />
    </div>
  );
}
const nodeTypes = { service: ServiceNode };
export default function ImpactGraph({
  preview,
  selected,
  onSelect,
  depth,
  full,
}: {
  preview: Preview;
  selected: string;
  onSelect: (id: string) => void;
  depth: number;
  full: Topology | null;
}) {
  const graph = useMemo(() => {
    const path = new Set(
      preview.impacts.find((i) => i.service_id === selected)
        ?.path_claim_ids[0] || [],
    );
    const items = full
      ? full.nodes.map((n, i) => ({
          service_id: n.id,
          name: n.name,
          depth: Math.floor(i / 10),
          owner_status: "company",
        }))
      : preview.impacts.filter((i) => i.depth <= depth);
    const bands = new Map<number, number>();
    const totals = new Map<number, number>();
    items.forEach((i) => totals.set(i.depth, (totals.get(i.depth) || 0) + 1));
    const nodes = items.map((i) => {
      const order = bands.get(i.depth) || 0;
      bands.set(i.depth, order + 1);
      return {
        id: i.service_id,
        type: "service",
        position: {
          x: i.depth * 245,
          y: order * 130 - ((totals.get(i.depth) || 1) - 1) * 65 + 230,
        },
        data: {
          name: i.name,
          depth: i.depth,
          root: preview.roots.includes(i.service_id),
          selected: i.service_id === selected,
          owner: i.owner_status,
        },
      };
    });
    const ids = new Set(items.map((i) => i.service_id));
    const edges = (full?.edges || preview.edges)
      .filter((e) => ids.has(e.source) && ids.has(e.target))
      .map((e) => ({
        id: e.claim_id,
        source: e.source,
        target: e.target,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: path.has(e.claim_id) ? "#9ebcff" : "#536785",
        },
        style: {
          stroke: path.has(e.claim_id) ? "#9ebcff" : "#445673",
          strokeWidth: path.has(e.claim_id) ? 2.5 : 1.3,
        },
        zIndex: path.has(e.claim_id) ? 2 : 0,
      }));
    return { nodes, edges };
  }, [preview, selected, depth, full]);
  return (
    <div
      className="graph-canvas"
      aria-label="Live source-backed dependency graph"
    >
      <ReactFlow
        key={String(!!full) + depth}
        nodes={graph.nodes}
        edges={graph.edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.13 }}
        minZoom={0.15}
        maxZoom={1.5}
        nodesDraggable={false}
        onNodeClick={(_, n) => onSelect(n.id)}
        proOptions={{ hideAttribution: false }}
      >
        <Background color="#354560" gap={24} size={0.7} />
        <Controls showInteractive={false} />
      </ReactFlow>
      <div className="graph-key">
        <span>
          <i className="blue-square" />
          Change root
        </span>
        <span>
          <i className="line-key" />
          Verified dependency
        </span>
        <span>
          <i className="amber-dot" />
          Ownership needs review
        </span>
      </div>
    </div>
  );
}
