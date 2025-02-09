import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";
import type { GridNode } from "@shared/schema";
import { PowerIcon, BatteryChargingIcon, GaugeIcon, Settings2Icon } from "lucide-react";

interface GridControlPanelProps {
  nodeId: number;
}

export default function GridControlPanel({ nodeId }: GridControlPanelProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [targetLoad, setTargetLoad] = useState<number>(0);

  const { data: node, isLoading } = useQuery<GridNode>({
    queryKey: ["/api/nodes", nodeId],
  });

  const updateControl = useMutation({
    mutationFn: async ({ controlMode, targetLoad }: { controlMode: string; targetLoad?: number }) => {
      await apiRequest(`/api/nodes/${nodeId}/control`, {
        method: "PATCH",
        body: { controlMode, targetLoad },
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/nodes", nodeId] });
      toast({
        title: "Control settings updated",
        description: "The grid node control settings have been updated successfully.",
      });
    },
  });

  if (isLoading || !node) {
    return null;
  }

  const isAutomatic = node.controlMode === "automatic";
  const efficiency = node.efficiency || 100;

  return (
    <Card className="col-span-1">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings2Icon className="h-5 w-5" />
          Component Control
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Status Indicators */}
        <div className="grid grid-cols-3 gap-4">
          <StatusCard
            icon={PowerIcon}
            title="Power"
            value={`${node.currentLoad} MW`}
            status={node.status}
          />
          <StatusCard
            icon={BatteryChargingIcon}
            title="Efficiency"
            value={`${efficiency}%`}
            status={efficiency > 90 ? "optimal" : efficiency > 75 ? "warning" : "critical"}
          />
          <StatusCard
            icon={GaugeIcon}
            title="Load"
            value={`${(node.currentLoad / node.capacity * 100).toFixed(1)}%`}
            status={node.currentLoad / node.capacity < 0.8 ? "optimal" : "warning"}
          />
        </div>

        {/* Control Mode Toggle */}
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h4 className="text-sm font-medium">Control Mode</h4>
            <p className="text-sm text-muted-foreground">
              {isAutomatic ? "Automatic optimization" : "Manual control"}
            </p>
          </div>
          <Switch
            checked={!isAutomatic}
            onCheckedChange={(checked) =>
              updateControl.mutate({ controlMode: checked ? "manual" : "automatic" })
            }
          />
        </div>

        {/* Manual Control Slider */}
        <div className="space-y-4">
          <div className="space-y-1">
            <h4 className="text-sm font-medium">Target Load</h4>
            <p className="text-sm text-muted-foreground">
              Set the desired power output level
            </p>
          </div>
          <Slider
            disabled={isAutomatic}
            min={0}
            max={node.capacity}
            step={1}
            value={[targetLoad]}
            onValueChange={([value]) => setTargetLoad(value)}
            className="py-4"
          />
          <div className="flex justify-between text-sm">
            <span>0 MW</span>
            <span>{targetLoad.toFixed(1)} MW</span>
            <span>{node.capacity} MW</span>
          </div>
          <Button
            disabled={isAutomatic}
            onClick={() => updateControl.mutate({ controlMode: "manual", targetLoad })}
            className="w-full"
          >
            Apply Changes
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

interface StatusCardProps {
  icon: React.ElementType;
  title: string;
  value: string;
  status: string;
}

function StatusCard({ icon: Icon, title, value, status }: StatusCardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case "online":
      case "optimal":
        return "text-green-400";
      case "warning":
        return "text-yellow-400";
      case "offline":
      case "critical":
        return "text-red-400";
      default:
        return "text-blue-400";
    }
  };

  return (
    <div className="rounded-lg bg-card p-4 space-y-2">
      <div className="flex items-center justify-between">
        <Icon className={`h-5 w-5 ${getStatusColor(status)}`} />
        <div className={`h-2 w-2 rounded-full ${getStatusColor(status)}`} />
      </div>
      <div className="space-y-1">
        <p className="text-sm font-medium">{title}</p>
        <p className="text-xl font-bold">{value}</p>
      </div>
    </div>
  );
}
