import { Switch, Route } from "wouter";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "./lib/queryClient";
import { Toaster } from "@/components/ui/toaster";
import { GridProvider } from "@/context/GridContext";
import NotFound from "@/pages/not-found";
import MapView from "@/pages/MapView";
import SystemView from "@/pages/SystemView";
import Analytics from "@/pages/Analytics";

function Router() {
  return (
    <Switch>
      <Route path="/" component={MapView} />
      <Route path="/system" component={SystemView} />
      <Route path="/analytics" component={Analytics} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <GridProvider>
        <Router />
        <Toaster />
      </GridProvider>
    </QueryClientProvider>
  );
}

export default App;