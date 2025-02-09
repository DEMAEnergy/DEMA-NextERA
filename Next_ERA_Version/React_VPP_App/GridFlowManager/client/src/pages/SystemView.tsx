import { useQuery } from "@tanstack/react-query";
import ReactFlow, { 
  Background, 
  Controls,
  MarkerType,
  type Node,
  type Edge,
} from "reactflow";
import "reactflow/dist/style.css";
import { useGrid } from "@/context/GridContext";
import DashboardLayout, { MetricsOverlay } from "@/components/layout/DashboardLayout";
import GridControlPanel from "@/components/control/GridControlPanel";
import type { GridNode, GridConnection } from "@shared/schema";

function createFlowElements(nodes: GridNode[], connections: GridConnection[], selectedNodeId?: number) {
  const flowNodes = nodes.map((node) => ({
    id: node.id.toString(),
    data: {
      ...node,
      selected: node.id === selectedNodeId,
    },
    position: { x: node.longitude * 100, y: node.latitude * 100 },
    type: "default",
  }));

  const flowEdges = connections.map((conn) => ({
    id: `grid-${conn.id}`,
    source: conn.fromNodeId.toString(),
    target: conn.toNodeId.toString(),
    type: "default",
    markerEnd: { type: MarkerType.Arrow },
    label: `${conn.currentLoad}/${conn.capacity} MW`,
    style: { stroke: conn.status === "overloaded" ? "#ef4444" : "#93c5fd" },
  }));

  return { nodes: flowNodes, edges: flowEdges };
}

export default function SystemView() {
  const { selectedNode, setSelectedNode, showOnMap } = useGrid();

  const { data: nodes } = useQuery<GridNode[]>({
    queryKey: ["/api/nodes"],
  });

  const { data: connections } = useQuery<GridConnection[]>({
    queryKey: ["/api/connections"],
  });

  const elements = createFlowElements(
    nodes || [], 
    connections || [],
    selectedNode?.id
  );

  const handleNodeClick = (event: any, node: Node) => {
    const gridNode = nodes?.find(n => n.id.toString() === node.id);
    if (gridNode) {
      setSelectedNode(gridNode);
    }
  };

  return (
    <DashboardLayout 
      title="System Diagram" 
      location="Saudi Arabia Power Grid"
      className="p-0"
    >
      <div className="h-full w-full">
        <ReactFlow
          nodes={elements.nodes}
          edges={elements.edges}
          onNodeClick={handleNodeClick}
          fitView
        >
          <Background />
          <Controls className="!z-[50]" />
        </ReactFlow>
      </div>

      {selectedNode && (
        <div className="fixed right-4 top-20 z-[100] w-96">
          <div className="bg-background/80 backdrop-blur-sm rounded-lg shadow-xl border border-border/50 p-4">
            <div className="space-y-4">
              <div>
                <h3 className="font-medium">{selectedNode.name}</h3>
                <p className="text-sm text-muted-foreground">Type: {selectedNode.type}</p>
                <p className="text-sm text-muted-foreground">
                  Load: {selectedNode.currentLoad}/{selectedNode.capacity} MW
                </p>
              </div>
              <button
                onClick={() => showOnMap(selectedNode)}
                className="w-full px-4 py-2 text-sm font-medium text-center text-primary-foreground bg-primary rounded-md hover:bg-primary/90"
              >
                Show on Map
              </button>
            </div>
          </div>
        </div>
      )}

      <MetricsOverlay />
    </DashboardLayout>
  );
}