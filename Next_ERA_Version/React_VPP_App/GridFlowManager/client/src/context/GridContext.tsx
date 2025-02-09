import { createContext, useContext, useState, useCallback } from "react";
import { useLocation } from "wouter";
import type { GridNode, GridConnection } from "@shared/schema";

interface MapPosition {
  center: [number, number];
  zoom: number;
}

interface GridContextType {
  selectedNode?: GridNode;
  setSelectedNode: (node?: GridNode) => void;
  showOnMap: (node: GridNode) => void;
  showOnSystem: (node: GridNode) => void;
  mapPosition: MapPosition;
  setMapPosition: (position: MapPosition) => void;
}

const GridContext = createContext<GridContextType | null>(null);

export function GridProvider({ children }: { children: React.ReactNode }) {
  const [selectedNode, setSelectedNode] = useState<GridNode>();
  const [, setLocation] = useLocation();
  const [mapPosition, setMapPosition] = useState<MapPosition>({
    center: [24.7136, 46.6753], // Default to Riyadh
    zoom: 6
  });

  const showOnMap = useCallback((node: GridNode) => {
    setSelectedNode(node);
    setMapPosition({
      center: [node.latitude, node.longitude],
      zoom: 12
    });
    setLocation(`/?nodeId=${node.id}`);
  }, [setLocation]);

  const showOnSystem = useCallback((node: GridNode) => {
    setSelectedNode(node);
    setLocation(`/system?nodeId=${node.id}`);
  }, [setLocation]);

  return (
    <GridContext.Provider value={{
      selectedNode,
      setSelectedNode,
      showOnMap,
      showOnSystem,
      mapPosition,
      setMapPosition,
    }}>
      {children}
    </GridContext.Provider>
  );
}

export function useGrid() {
  const context = useContext(GridContext);
  if (!context) {
    throw new Error("useGrid must be used within a GridProvider");
  }
  return context;
}