export type ChatRole = 'user' | 'assistant';

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  createdAt: string;
}

export interface SendMessagePayload {
  message: string;
}

export interface SendMessageResponse {
  reply: string;
  conversationId?: string;
}
