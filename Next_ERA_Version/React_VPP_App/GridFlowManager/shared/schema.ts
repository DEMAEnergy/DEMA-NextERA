import { pgTable, text, serial, integer, real, timestamp, boolean } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const gridNodes = pgTable("grid_nodes", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  type: text("type").notNull(), // 'generator', 'consumer', 'storage'
  latitude: real("latitude").notNull(),
  longitude: real("longitude").notNull(),
  capacity: real("capacity").notNull(), // in MW
  currentLoad: real("current_load").notNull(), // in MW
  status: text("status").notNull(), // 'online', 'offline', 'maintenance'
  controlMode: text("control_mode").notNull().default('automatic'), // 'automatic', 'manual'
  targetLoad: real("target_load"), // Target load when in manual mode
  efficiency: real("efficiency").notNull().default(100), // Efficiency percentage
  lastControlUpdate: timestamp("last_control_update"),
});

export const gridConnections = pgTable("grid_connections", {
  id: serial("id").primaryKey(),
  fromNodeId: integer("from_node_id").notNull(),
  toNodeId: integer("to_node_id").notNull(),
  capacity: real("capacity").notNull(), // in MW
  currentLoad: real("current_load").notNull(), // in MW
  status: text("status").notNull(), // 'active', 'inactive', 'overloaded'
  controlEnabled: boolean("control_enabled").notNull().default(true),
});

export const powerMetrics = pgTable("power_metrics", {
  id: serial("id").primaryKey(),
  nodeId: integer("node_id").notNull(),
  timestamp: timestamp("timestamp").notNull(),
  demand: real("demand").notNull(), // in MW
  supply: real("supply").notNull(), // in MW
  frequency: real("frequency").notNull(), // in Hz
});

export const insertGridNodeSchema = createInsertSchema(gridNodes).omit({ id: true });
export const insertGridConnectionSchema = createInsertSchema(gridConnections).omit({ id: true });
export const insertPowerMetricSchema = createInsertSchema(powerMetrics).omit({ id: true });

export type GridNode = typeof gridNodes.$inferSelect;
export type GridConnection = typeof gridConnections.$inferSelect;
export type PowerMetric = typeof powerMetrics.$inferSelect;

export type InsertGridNode = z.infer<typeof insertGridNodeSchema>;
export type InsertGridConnection = z.infer<typeof insertGridConnectionSchema>;
export type InsertPowerMetric = z.infer<typeof insertPowerMetricSchema>;

// Control interface types
export const updateGridNodeControlSchema = z.object({
  controlMode: z.enum(['automatic', 'manual']),
  targetLoad: z.number().optional(),
});

export type UpdateGridNodeControl = z.infer<typeof updateGridNodeControlSchema>;