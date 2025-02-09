// Types for our load profile data
export interface LoadProfileData {
  timestamp: number;
  baseLoad: number[];
  withDR: number[];
}

class LoadProfileService {
  private ws: WebSocket | null = null;
  private subscribers: ((data: LoadProfileData) => void)[] = [];

  constructor(
    private wsUrl: string = 'ws://localhost:3001/ws',
    private restUrl: string = 'http://localhost:3001'
  ) {
    this.connect();
  }

  private connect() {
    this.ws = new WebSocket(this.wsUrl);
    
    this.ws.onopen = () => {
      console.log('Connected to load profile service');
    };

    this.ws.onmessage = (event) => {
      try {
        const data: LoadProfileData = JSON.parse(event.data);
        this.notifySubscribers(data);
      } catch (error) {
        console.error('Error parsing load profile data:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('Disconnected from load profile service');
      // Attempt to reconnect after 5 seconds
      setTimeout(() => this.connect(), 5000);
    };
  }

  subscribe(callback: (data: LoadProfileData) => void) {
    this.subscribers.push(callback);
    return () => {
      this.subscribers = this.subscribers.filter(cb => cb !== callback);
    };
  }

  private notifySubscribers(data: LoadProfileData) {
    this.subscribers.forEach(callback => callback(data));
  }

  // For REST fallback if WebSocket is not available
  async fetchLatestData(): Promise<LoadProfileData> {
    const response = await fetch(`${this.restUrl}/api/load-profile`);
    if (!response.ok) {
      throw new Error('Failed to fetch load profile data');
    }
    return response.json();
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// Export singleton instance
export const loadProfileService = new LoadProfileService(); 