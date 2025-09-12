/**
 * Notification Service Client SDK
 */

interface NotificationConfig {
  wsUrl: string;
  apiUrl: string;
  token: string;
  replayId?: string;
}

interface NotificationRequest {
  to: string | string[];
  subject?: string;
  body: string;
  type?: 'email' | 'sms' | 'push';
  priority?: 'low' | 'normal' | 'high';
  template?: string;
  data?: Record<string, unknown>;
}

interface NotificationResponse {
  id: string;
  status: 'sent' | 'pending' | 'failed';
  message?: string;
}

interface NotificationMessage {
  id: string;
  type: string;
  timestamp: string;
  data: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

export class NotificationClient {
  private ws?: WebSocket;
  private config: NotificationConfig;
  private messageHandlers: Map<
    string,
    ((message: NotificationMessage) => void)[]
  > = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(config: NotificationConfig) {
    this.config = config;
  }

  /**
   * Connect to WebSocket
   */
  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const wsUrl = new URL(this.config.wsUrl);
      wsUrl.searchParams.set('token', this.config.token);

      if (this.config.replayId) {
        wsUrl.searchParams.set('replay_id', this.config.replayId);
      }

      this.ws = new WebSocket(wsUrl.toString());

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        resolve();
      };

      this.ws.onmessage = event => {
        try {
          const message: NotificationMessage = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('Failed to parse message:', error);
        }
      };

      this.ws.onerror = error => {
        console.error('WebSocket error:', error);
        reject(error);
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.handleReconnect();
      };
    });
  }

  /**
   * Handle incoming message
   */
  private handleMessage(message: NotificationMessage): void {
    // Handle heartbeat
    if (message.type === 'heartbeat') {
      this.ws?.send(JSON.stringify({ type: 'pong' }));
      return;
    }

    // Store replay ID
    if (message.id) {
      this.config.replayId = message.id;
      localStorage.setItem('notification_replay_id', message.id);
    }

    // Call registered handlers
    const handlers = this.messageHandlers.get(message.type) || [];
    handlers.forEach(handler => handler(message));

    // Call generic handlers
    const allHandlers = this.messageHandlers.get('*') || [];
    allHandlers.forEach(handler => handler(message));
  }

  /**
   * Register message handler
   */
  on(type: string, handler: (message: NotificationMessage) => void): void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, []);
    }
    this.messageHandlers.get(type)!.push(handler);
  }

  /**
   * Subscribe to push notifications
   */
  async subscribePush(subscription: PushSubscription): Promise<void> {
    const response = await fetch(`${this.config.apiUrl}/push/subscribe`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.config.token}`,
      },
      body: JSON.stringify(subscription.toJSON()),
    });

    if (!response.ok) {
      throw new Error(`Push subscription failed: ${response.statusText}`);
    }
  }

  /**
   * Send notification
   */
  async sendNotification(
    request: NotificationRequest
  ): Promise<NotificationResponse> {
    const response = await fetch(`${this.config.apiUrl}/notify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.config.token}`,
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Send notification failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Handle reconnection
   */
  private handleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    console.log(
      `Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`
    );

    setTimeout(() => {
      this.connect().catch(error => {
        console.error('Reconnection failed:', error);
      });
    }, delay);
  }

  /**
   * Disconnect WebSocket
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = undefined;
    }
  }
}
