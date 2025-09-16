import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Alert, Box, Divider, Stack, Typography } from '@mui/material';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import { ChatMessage } from '../types/chat';
import { sendMessage } from '../services/api';

const ChatInterface = (): JSX.Element => {
  const createId = useCallback(() => {
    if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
      return crypto.randomUUID();
    }

    return Math.random().toString(36).slice(2);
  }, []);

  const [messages, setMessages] = useState<ChatMessage[]>(() => [
    {
      id: createId(),
      role: 'assistant',
      content: 'سلام! من دستیار مالی چت حساب هستم. برای شروع، وضعیت مالی یا سوال خود را بپرسید.',
      createdAt: new Date().toISOString(),
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const scrollToBottom = useCallback(() => {
    const container = containerRef.current;
    if (!container) {
      return;
    }

    container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSendMessage = useCallback(
    async (content: string) => {
      const userMessage: ChatMessage = {
        id: createId(),
        role: 'user',
        content,
        createdAt: new Date().toISOString(),
      };

      setMessages((previous) => [...previous, userMessage]);
      setError(null);
      setIsLoading(true);

      abortControllerRef.current?.abort();
      const controller = new AbortController();
      abortControllerRef.current = controller;

      try {
        const response = await sendMessage(content, controller.signal);
        const assistantMessage: ChatMessage = {
          id: createId(),
          role: 'assistant',
          content: response.reply,
          createdAt: new Date().toISOString(),
        };

        setMessages((previous) => [...previous, assistantMessage]);
      } catch (apiError) {
        setError(apiError instanceof Error ? apiError.message : 'خطای نامشخصی رخ داده است.');
      } finally {
        setIsLoading(false);
      }
    },
    [createId],
  );

  const hasMessages = useMemo(() => messages.length > 0, [messages]);

  return (
    <Stack spacing={2}>
      <Box>
        <Typography variant="h5" sx={{ fontWeight: 600 }} gutterBottom>
          گفتگو با دستیار مالی
        </Typography>
        <Typography variant="body2" color="text.secondary">
          سوالات مالی خود را مطرح کنید تا با تحلیل داده‌های شما، بهترین پیشنهاد ارائه شود.
        </Typography>
      </Box>

      <Divider />

      {error && (
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Box ref={containerRef} sx={{ flexGrow: 1, overflow: 'hidden' }}>
        {hasMessages && <MessageList messages={messages} isLoading={isLoading} />}
      </Box>

      <MessageInput onSend={handleSendMessage} disabled={isLoading} />
    </Stack>
  );
};

export default ChatInterface;
