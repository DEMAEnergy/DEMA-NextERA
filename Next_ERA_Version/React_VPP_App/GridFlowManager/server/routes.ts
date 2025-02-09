import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { insertGridNodeSchema, updateGridNodeControlSchema } from "@shared/schema";

export function registerRoutes(app: Express): Server {
  // Grid Nodes
  app.get("/api/nodes", async (_req, res) => {
    const nodes = await storage.getGridNodes();
    res.json(nodes);
  });

  app.get("/api/nodes/:id", async (req, res) => {
    const node = await storage.getGridNode(parseInt(req.params.id));
    if (!node) {
      res.status(404).json({ message: "Node not found" });
      return;
    }
    res.json(node);
  });

  // Add POST endpoint for creating new nodes
  app.post("/api/nodes", async (req, res) => {
    try {
      console.log('Received node creation request:', req.body); // Debug log
      const newNode = insertGridNodeSchema.parse(req.body);
      const createdNode = await storage.createGridNode(newNode);
      console.log('Created node:', createdNode); // Debug log
      res.json(createdNode);
    } catch (error) {
      console.error('Error creating node:', error);
      res.status(400).json({ message: "Invalid node data", error: String(error) });
    }
  });

  // Existing endpoint for updating node control settings
  app.patch("/api/nodes/:id/control", async (req, res) => {
    const id = parseInt(req.params.id);
    const node = await storage.getGridNode(id);
    if (!node) {
      res.status(404).json({ message: "Node not found" });
      return;
    }

    try {
      const control = updateGridNodeControlSchema.parse(req.body);
      const updatedNode = await storage.updateGridNodeControl(id, control);
      res.json(updatedNode);
    } catch (error) {
      res.status(400).json({ message: "Invalid control parameters" });
    }
  });

  // Grid Connections
  app.get("/api/connections", async (_req, res) => {
    const connections = await storage.getGridConnections();
    res.json(connections);
  });

  app.get("/api/connections/:id", async (req, res) => {
    const connection = await storage.getGridConnection(parseInt(req.params.id));
    if (!connection) {
      res.status(404).json({ message: "Connection not found" });
      return;
    }
    res.json(connection);
  });

  // Power Metrics
  app.get("/api/metrics/:nodeId", async (req, res) => {
    const limit = req.query.limit ? parseInt(req.query.limit as string) : undefined;
    const metrics = await storage.getPowerMetrics(parseInt(req.params.nodeId), limit);
    res.json(metrics);
  });

  const httpServer = createServer(app);
  return httpServer;
}