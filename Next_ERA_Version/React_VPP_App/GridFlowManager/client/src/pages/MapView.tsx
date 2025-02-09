import { useState, useEffect, useCallback } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import DashboardLayout, { MetricsOverlay } from "@/components/layout/DashboardLayout";
import MapSettings, { type MapProvider } from "@/components/map/MapSettings";
import NodeForm from "@/components/map/NodeForm";
import type { GridNode, InsertGridNode } from "@shared/schema";
import { useGrid } from "@/context/GridContext";
import { queryClient } from "@/lib/queryClient";

// Fix Leaflet default marker icon
import L from "leaflet";
import icon from "leaflet/dist/images/marker-icon.png";
import iconShadow from "leaflet/dist/images/marker-shadow.png";

const DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});
L.Marker.prototype.options.icon = DefaultIcon;

// Map providers configuration
interface MapProviderConfig {
  url: string;
  attribution: string;
  subdomains?: string[];
  accessToken?: string;
}

const mapProviders: Record<MapProvider, MapProviderConfig> = {
  osm: {
    url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  },
  google: {
    url: "http://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
    attribution: "&copy; Google Maps",
    subdomains: ["mt0", "mt1", "mt2", "mt3"],
  },
  mapbox: {
    url: "https://api.mapbox.com/styles/v1/mapbox/dark-v11/tiles/{z}/{x}/{y}",
    attribution: '&copy; <a href="https://www.mapbox.com/">Mapbox</a>',
    accessToken: import.meta.env.VITE_MAPBOX_TOKEN,
  },
  esri: {
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attribution: "&copy; ESRI",
  },
};

// Custom dark map style for OSM
const mapStyle = {
  dark: {
    filter: [
      'invert(95%)',
      'hue-rotate(180deg)',
      'brightness(0.8)',
      'contrast(1.2)',
      'saturate(0.5)'
    ].join(' ')
  }
};

// Custom map controls component
function MapControls() {
  const map = useMap();
  map.getContainer().style.background = 'hsl(222, 47%, 11%)';
  return null;
}

// MapEvents component to handle map clicks
function MapEvents({ onMapClick }: { onMapClick: (lat: number, lng: number) => void }) {
  useMapEvents({
    click: (e) => {
      console.log('Map clicked at:', e.latlng); // Debug log
      const { lat, lng } = e.latlng;
      onMapClick(lat, lng);
    },
  });
  return null;
}

// Add MapCenterUpdate component to handle map centering
function MapCenterUpdate({ center, zoom }: { center: [number, number], zoom: number }) {
  const map = useMap();

  useEffect(() => {
    map.setView(center, zoom);
  }, [map, center, zoom]);

  return null;
}

export default function MapView() {
  const [mapProvider, setMapProvider] = useState<MapProvider>("mapbox");
  const { selectedNode, setSelectedNode, showOnSystem, mapPosition, setMapPosition } = useGrid();
  const [isAddingNode, setIsAddingNode] = useState(false);
  const [clickedPosition, setClickedPosition] = useState<{ lat: number; lng: number } | null>(null);

  // Map event handler to update position
  const handleMapMove = useCallback(() => {
    const map = document.querySelector('.leaflet-container')?.__leaflet_map__;
    if (map) {
      const center = map.getCenter();
      console.log('Map moved to:', { lat: center.lat, lng: center.lng, zoom: map.getZoom() }); // Debug log
      setMapPosition({
        center: [center.lat, center.lng],
        zoom: map.getZoom()
      });
    }
  }, [setMapPosition]);

  // Debug log initial map position
  useEffect(() => {
    console.log('Initial map position:', mapPosition);
  }, [mapPosition]);

  // Validate Mapbox token if Mapbox is selected
  useEffect(() => {
    if (mapProvider === "mapbox" && !import.meta.env.VITE_MAPBOX_TOKEN) {
      console.warn("Mapbox token not found. Defaulting to OpenStreetMap.");
      setMapProvider("osm");
    }
  }, [mapProvider]);

  const { data: nodes } = useQuery<GridNode[]>({
    queryKey: ["/api/nodes"],
  });

  console.log('Current nodes:', nodes); // Debug log

  const { data: powerLines = [] } = useQuery({
    queryKey: ["/api/power-lines"],
    queryFn: async () => {
      try {
        const query = `
          [out:json][timeout:25];
          area["name:en"="Riyadh"]["admin_level"="4"]->.searchArea;
          (
            way["power"="line"](area.searchArea);
            >;
          );
          out body;
        `;

        const res = await fetch("https://overpass-api.de/api/interpreter", {
          method: "POST",
          body: query,
        });

        if (!res.ok) {
          console.error("Failed to fetch power lines");
          return [];
        }

        const data = await res.json();
        const nodesMap = new Map(
          data.elements
            .filter((el: any) => el.type === "node")
            .map((node: any) => [
              node.id,
              { lat: node.lat, lon: node.lon }
            ])
        );

        return data.elements
          .filter((el: any) => el.type === "way")
          .map((way: any) => ({
            id: way.id,
            coordinates: way.nodes
              .map((nodeId: number) => {
                const node = nodesMap.get(nodeId);
                return node ? [node.lat, node.lon] as [number, number] : null;
              })
              .filter(Boolean),
            voltage: way.tags?.voltage,
          }));
      } catch (error) {
        console.error("Error fetching power lines:", error);
        return [];
      }
    },
  });

  const provider = mapProviders[mapProvider];
  const tileLayerProps = {
    url: provider.url,
    attribution: provider.attribution,
    ...(provider.subdomains && { subdomains: provider.subdomains }),
    ...(provider.accessToken && {
      url: `${provider.url}?access_token=${provider.accessToken}`,
    }),
  };

  const handleMarkerClick = (node: GridNode) => {
    setSelectedNode(node);
  };

  const createNodeMutation = useMutation({
    mutationFn: async (newNode: InsertGridNode) => {
      console.log('Creating new node:', newNode); // Debug log
      const response = await fetch("/api/nodes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newNode),
      });
      if (!response.ok) {
        const errorData = await response.json();
        console.error('Server error:', errorData); // Debug log
        throw new Error(`Failed to create node: ${errorData.message || 'Unknown error'}`);
      }
      const data = await response.json();
      console.log('Node created:', data); // Debug log
      return data;
    },
    onSuccess: () => {
      console.log('Invalidating queries...'); // Debug log
      queryClient.invalidateQueries({ queryKey: ["/api/nodes"] });
    },
  });

  const handleCreateNode = async (data: InsertGridNode) => {
    console.log('handleCreateNode called with:', data); // Debug log
    await createNodeMutation.mutateAsync(data);
  };

  const handleMapClick = (lat: number, lng: number) => {
    console.log('Setting clicked position:', { lat, lng }); // Debug log
    setClickedPosition({ lat, lng });
    setIsAddingNode(true);
  };

  return (
    <DashboardLayout
      title="Virtual Power Plant"
      location="Riyadh City"
      className="p-0"
    >
      <div className="absolute inset-0 z-0">
        <MapContainer
          center={mapPosition.center}
          zoom={mapPosition.zoom}
          className="h-full w-full"
          zoomControl={false}
          attributionControl={false}
          whenReady={(map) => {
            console.log('Map ready, setting up event listeners'); // Debug log
            map.target.on('moveend', handleMapMove);
            map.target.on('zoomend', handleMapMove);
          }}
        >
          <TileLayer
            {...tileLayerProps}
            className={mapProvider === "osm" ? "map-tiles" : ""}
          />

          <MapEvents onMapClick={handleMapClick} />
          <MapControls />
          <MapCenterUpdate center={mapPosition.center} zoom={mapPosition.zoom} />

          {nodes?.map((node) => (
            <Marker
              key={node.id}
              position={[node.latitude, node.longitude]}
              title={node.name}
              eventHandlers={{
                click: () => handleMarkerClick(node),
              }}
            >
              <Popup className="dark-popup">
                <div className="p-2 space-y-2">
                  <h3 className="font-bold">{node.name}</h3>
                  <p className="text-sm">Type: {node.type}</p>
                  <p className="text-sm">
                    Load: {node.currentLoad}/{node.capacity} MW
                  </p>
                  <p className="text-sm">Status: {node.status}</p>
                  <button
                    onClick={() => showOnSystem(node)}
                    className="w-full px-2 py-1 text-sm font-medium text-center text-primary-foreground bg-primary rounded-md hover:bg-primary/90"
                  >
                    Show in System View
                  </button>
                </div>
              </Popup>
            </Marker>
          ))}

          {powerLines.map((line: any) => (
            <Polyline
              key={line.id}
              positions={line.coordinates}
              color="#3b82f6"
              weight={2}
              opacity={0.8}
            />
          ))}
        </MapContainer>
      </div>

      {clickedPosition && (
        <NodeForm
          isOpen={isAddingNode}
          onClose={() => {
            setIsAddingNode(false);
            setClickedPosition(null);
          }}
          position={clickedPosition}
          onSubmit={handleCreateNode}
        />
      )}

      <MapSettings provider={mapProvider} onProviderChange={setMapProvider} />
      <MetricsOverlay />
    </DashboardLayout>
  );
}