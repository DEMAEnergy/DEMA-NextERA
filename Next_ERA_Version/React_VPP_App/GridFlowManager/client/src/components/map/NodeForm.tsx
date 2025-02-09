import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { insertGridNodeSchema, type InsertGridNode } from "@shared/schema";

interface NodeFormProps {
  isOpen: boolean;
  onClose: () => void;
  position: { lat: number; lng: number };
  onSubmit: (data: InsertGridNode) => void;
}

export default function NodeForm({ isOpen, onClose, position, onSubmit }: NodeFormProps) {
  const { toast } = useToast();
  const form = useForm<InsertGridNode>({
    resolver: zodResolver(insertGridNodeSchema),
    defaultValues: {
      name: "",
      type: "generator",
      latitude: position.lat,
      longitude: position.lng,
      capacity: 100,
      currentLoad: 0,
      status: "online",
      controlMode: "automatic",
      efficiency: 100,
    },
  });

  const handleSubmit = (data: InsertGridNode) => {
    console.log('Submitting node with coordinates:', { lat: position.lat, lng: position.lng }); // Debug log
    try {
      onSubmit({
        ...data,
        latitude: position.lat,
        longitude: position.lng
      });
      form.reset();
      onClose();
      toast({
        title: "Success",
        description: "Grid node created successfully",
      });
    } catch (error) {
      console.error('Error creating node:', error);
      toast({
        title: "Error",
        description: "Failed to create grid node",
        variant: "destructive",
      });
    }
  };

  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent side="right">
        <SheetHeader>
          <SheetTitle>Add Grid Node</SheetTitle>
        </SheetHeader>
        <div className="mb-4 p-2 bg-muted/50 rounded-md">
          <p className="text-sm text-muted-foreground">
            Selected Location: {position.lat.toFixed(6)}°, {position.lng.toFixed(6)}°
          </p>
        </div>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input placeholder="Enter node name" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Type</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select node type" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="generator">Generator</SelectItem>
                      <SelectItem value="consumer">Consumer</SelectItem>
                      <SelectItem value="storage">Storage</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="capacity"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Capacity (MW)</FormLabel>
                  <FormControl>
                    <Input type="number" {...field} onChange={e => field.onChange(parseFloat(e.target.value))} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="currentLoad"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Current Load (MW)</FormLabel>
                  <FormControl>
                    <Input type="number" {...field} onChange={e => field.onChange(parseFloat(e.target.value))} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="status"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Status</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select status" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="online">Online</SelectItem>
                      <SelectItem value="offline">Offline</SelectItem>
                      <SelectItem value="maintenance">Maintenance</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <Button type="submit" className="w-full">Create Node</Button>
          </form>
        </Form>
      </SheetContent>
    </Sheet>
  );
}