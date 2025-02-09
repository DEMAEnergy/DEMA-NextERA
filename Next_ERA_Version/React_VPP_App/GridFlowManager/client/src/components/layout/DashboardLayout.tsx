import { format } from "date-fns";
import { SunMedium } from "lucide-react";
import { cn } from "@/lib/utils";
import Sidebar from "./Sidebar";

interface DashboardLayoutProps {
  title: string;
  location?: string;
  children: React.ReactNode;
  className?: string;
}

export default function DashboardLayout({ 
  title, 
  location = "Riyadh City", 
  children,
  className 
}: DashboardLayoutProps) {
  return (
    <div className="relative h-screen overflow-hidden bg-background">
      {/* Main content area - full screen with lower z-index */}
      <main className={cn("h-screen w-full relative z-0", className)}>
        {children}

        {/* Floating header with high z-index */}
        <div className="fixed top-4 left-20 right-4 z-50">
          <div className="bg-background/80 backdrop-blur-sm rounded-lg shadow-xl border border-border/50">
            <div className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-2xl font-bold">{title}</h1>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <SunMedium className="h-4 w-4" />
                    <span>{location}</span>
                    <span>•</span>
                    <span>{format(new Date(), "HH:mm:ss")}</span>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">Live</span>
                    <div className="h-2 w-2 rounded-full bg-success animate-pulse" />
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">100ms</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar - highest z-index */}
        <div className="fixed left-0 top-0 h-full z-[60]">
          <Sidebar />
        </div>
      </main>
    </div>
  );
}

// Floating metrics overlay component
export function MetricsOverlay() {
  return (
    <div className="fixed bottom-4 left-20 right-4 z-50">
      <div className="bg-background/80 backdrop-blur-sm rounded-lg shadow-xl border border-border/50">
        <div className="p-4">
          <div className="grid grid-cols-4 gap-4">
            <MetricCard 
              title="Total Load"
              value="295"
              unit="GW"
              color="text-blue-400"
            />
            <MetricCard 
              title="Available"
              value="35"
              unit="GW"
              color="text-blue-500"
            />
            <MetricCard 
              title="Cost"
              value="0.24"
              unit="SR"
              color="text-yellow-400"
            />
            <MetricCard 
              title="Emergency Alert"
              value="95"
              unit="%"
              color="text-red-400"
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, unit, color }: { title: string; value: string; unit: string; color: string }) {
  return (
    <div className="text-center">
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      <div className="text-xs text-muted-foreground">{unit}</div>
      <div className="mt-1 text-sm font-medium">{title}</div>
    </div>
  );
}