import { Link, useLocation } from "wouter";
import { MapIcon, GitCommitHorizontal, BarChart3, ChevronLeftIcon, ChevronRightIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useState } from "react";

const navItems = [
  { href: "/", icon: MapIcon, label: "Network Map" },
  { href: "/system", icon: GitCommitHorizontal, label: "System View" },
  { href: "/analytics", icon: BarChart3, label: "Analytics" },
];

export default function Sidebar() {
  const [location] = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div
      className={cn(
        "h-screen bg-background/80 backdrop-blur-sm text-foreground transition-all duration-300 shadow-xl border-r border-border/50",
        collapsed ? "w-16" : "w-64"
      )}
    >
      <div className={cn("p-6", collapsed && "p-4")}>
        <h1 className={cn(
          "text-xl font-bold transition-opacity duration-300",
          collapsed && "opacity-0"
        )}>
          Grid Control
        </h1>
      </div>

      <Button
        variant="ghost"
        size="icon"
        className="absolute -right-4 top-6 h-8 w-8 rounded-full border bg-background shadow-md"
        onClick={() => setCollapsed(!collapsed)}
      >
        {collapsed ? (
          <ChevronRightIcon className="h-4 w-4" />
        ) : (
          <ChevronLeftIcon className="h-4 w-4" />
        )}
      </Button>

      <nav className={cn("space-y-2", collapsed ? "px-2" : "px-4")}>
        {navItems.map(({ href, icon: Icon, label }) => (
          <Link key={href} href={href}>
            <div
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors cursor-pointer",
                location === href
                  ? "bg-accent text-accent-foreground"
                  : "hover:bg-accent/50 hover:text-accent-foreground"
              )}
            >
              <Icon className="h-4 w-4 flex-shrink-0" />
              <span className={cn(
                "transition-opacity duration-300",
                collapsed && "opacity-0 w-0 hidden"
              )}>
                {label}
              </span>
            </div>
          </Link>
        ))}
      </nav>
    </div>
  );
}