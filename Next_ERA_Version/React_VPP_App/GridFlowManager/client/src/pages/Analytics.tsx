import { useQuery } from "@tanstack/react-query";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { format } from "date-fns";
import DashboardLayout, { MetricsOverlay } from "@/components/layout/DashboardLayout";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { PowerMetric } from "@shared/schema";

export default function Analytics() {
  const { data: metrics, isLoading } = useQuery<PowerMetric[]>({
    queryKey: ["/api/metrics/1", { limit: 24 }],
  });

  if (isLoading) {
    return (
      <DashboardLayout title="Analytics" location="Grid Performance">
        <div className="p-6">
          <Skeleton className="h-[800px] w-full" />
        </div>
      </DashboardLayout>
    );
  }

  const formattedData = metrics?.map(metric => ({
    ...metric,
    time: format(new Date(metric.timestamp), "HH:mm"),
  }));

  return (
    <DashboardLayout title="Analytics" location="Grid Performance">
      <div className="p-6 space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Power Demand vs Supply</CardTitle>
          </CardHeader>
          <CardContent className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={formattedData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="demand"
                  stroke="#ef4444"
                  name="Demand (MW)"
                />
                <Line
                  type="monotone"
                  dataKey="supply"
                  stroke="#22c55e"
                  name="Supply (MW)"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Grid Frequency</CardTitle>
          </CardHeader>
          <CardContent className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={formattedData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis domain={[59.8, 60.2]} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="frequency"
                  stroke="#3b82f6"
                  name="Frequency (Hz)"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <MetricsOverlay />
      </div>
    </DashboardLayout>
  );
}