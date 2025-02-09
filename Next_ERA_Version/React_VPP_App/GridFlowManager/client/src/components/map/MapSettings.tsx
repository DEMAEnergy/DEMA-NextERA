import { useState, useEffect } from "react";
import { Settings2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";

export type MapProvider = "osm" | "google" | "mapbox" | "esri";

interface MapSettingsProps {
  provider: MapProvider;
  onProviderChange: (provider: MapProvider) => void;
}

export default function MapSettings({ provider, onProviderChange }: MapSettingsProps) {
  const [isOpen, setIsOpen] = useState(false);
  const { toast } = useToast();

  const handleProviderChange = (value: string) => {
    if (value === "mapbox" && !import.meta.env.VITE_MAPBOX_TOKEN) {
      toast({
        title: "Mapbox token not found",
        description: "Please configure a Mapbox access token to use Mapbox maps.",
        variant: "destructive",
      });
      return;
    }
    onProviderChange(value as MapProvider);
  };

  return (
    <div className="fixed right-4 top-20 z-[100]">
      <div className="bg-background/80 backdrop-blur-sm rounded-lg shadow-xl border border-border/50 p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Settings2 className="h-4 w-4" />
            <h3 className="font-medium">Map Settings</h3>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => setIsOpen(!isOpen)}
          >
            <Settings2 className="h-4 w-4" />
          </Button>
        </div>

        {isOpen && (
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Map Provider</label>
              <Select value={provider} onValueChange={handleProviderChange}>
                <SelectTrigger>
                  <SelectValue placeholder="Select map provider" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="osm">OpenStreetMap</SelectItem>
                  <SelectItem value="google">Google Maps</SelectItem>
                  <SelectItem value="mapbox">Mapbox</SelectItem>
                  <SelectItem value="esri">ESRI World Imagery</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}