import { type GridNode, type GridConnection, type PowerMetric } from "@shared/schema";
import type { InsertGridNode, InsertGridConnection, InsertPowerMetric, UpdateGridNodeControl } from "@shared/schema";
import { gridNodes, gridConnections, powerMetrics } from "@shared/schema";
import { db } from "./db";
import { eq } from "drizzle-orm";

export interface IStorage {
  // Grid Nodes
  getGridNodes(): Promise<GridNode[]>;
  getGridNode(id: number): Promise<GridNode | undefined>;
  createGridNode(node: InsertGridNode): Promise<GridNode>;
  updateGridNodeControl(id: number, control: UpdateGridNodeControl): Promise<GridNode>;

  // Grid Connections
  getGridConnections(): Promise<GridConnection[]>;
  getGridConnection(id: number): Promise<GridConnection | undefined>;
  createGridConnection(connection: InsertGridConnection): Promise<GridConnection>;

  // Power Metrics
  getPowerMetrics(nodeId: number, limit?: number): Promise<PowerMetric[]>;
  createPowerMetric(metric: InsertPowerMetric): Promise<PowerMetric>;
}

export class DatabaseStorage implements IStorage {
  async getGridNodes(): Promise<GridNode[]> {
    return await db.select().from(gridNodes);
  }

  async getGridNode(id: number): Promise<GridNode | undefined> {
    const [node] = await db.select().from(gridNodes).where(eq(gridNodes.id, id));
    return node;
  }

  async createGridNode(node: InsertGridNode): Promise<GridNode> {
    console.log('Creating node with data:', node); // Debug log
    const [createdNode] = await db.insert(gridNodes).values(node).returning();
    console.log('Created node:', createdNode); // Debug log
    return createdNode;
  }

  async updateGridNodeControl(id: number, control: UpdateGridNodeControl): Promise<GridNode> {
    const [updatedNode] = await db
      .update(gridNodes)
      .set({
        controlMode: control.controlMode,
        targetLoad: control.targetLoad,
        lastControlUpdate: new Date(),
      })
      .where(eq(gridNodes.id, id))
      .returning();
    return updatedNode;
  }

  async getGridConnections(): Promise<GridConnection[]> {
    return await db.select().from(gridConnections);
  }

  async getGridConnection(id: number): Promise<GridConnection | undefined> {
    const [connection] = await db.select().from(gridConnections).where(eq(gridConnections.id, id));
    return connection;
  }

  async createGridConnection(connection: InsertGridConnection): Promise<GridConnection> {
    const [createdConnection] = await db.insert(gridConnections).values(connection).returning();
    return createdConnection;
  }

  async getPowerMetrics(nodeId: number, limit?: number): Promise<PowerMetric[]> {
    let query = db.select()
      .from(powerMetrics)
      .where(eq(powerMetrics.nodeId, nodeId))
      .orderBy(powerMetrics.timestamp);

    if (limit) {
      query = query.limit(limit);
    }

    return await query;
  }

  async createPowerMetric(metric: InsertPowerMetric): Promise<PowerMetric> {
    const [createdMetric] = await db.insert(powerMetrics).values(metric).returning();
    return createdMetric;
  }

  // Initialize demo data for Riyadh area
  async initializeDemoData() {
    // Create demo nodes in Riyadh area
    const solarFarm = await this.createGridNode({
      name: "Riyadh Solar Farm",
      type: "generator",
      latitude: 24.7136,
      longitude: 46.6753,
      capacity: 100,
      currentLoad: 75,
      status: "online",
      controlMode: "automatic",
      efficiency: 95,
    });

    const citySubstation = await this.createGridNode({
      name: "Riyadh City Substation",
      type: "consumer",
      latitude: 24.6877,
      longitude: 46.7219,
      capacity: 200,
      currentLoad: 150,
      status: "online",
      controlMode: "automatic",
      efficiency: 98,
    });

    // Create connection between nodes
    await this.createGridConnection({
      fromNodeId: solarFarm.id,
      toNodeId: citySubstation.id,
      capacity: 150,
      currentLoad: 75,
      status: "active",
      controlEnabled: true,
    });

    // Create historical metrics
    const now = new Date();
    for (let i = 0; i < 24; i++) {
      await this.createPowerMetric({
        nodeId: solarFarm.id,
        timestamp: new Date(now.getTime() - i * 3600000),
        demand: 50 + Math.random() * 50,
        supply: 75 + Math.random() * 25,
        frequency: 59.9 + Math.random() * 0.2,
      });
    }
  }
}

export const storage = new DatabaseStorage();

// Initialize demo data
storage.initializeDemoData().catch(console.error);