import { SendMessagePayload, SendMessageResponse } from '../types/chat';

const normalizeBaseUrl = (value: string | undefined) => {
  if (!value) {
    return '';
  }

  const trimmed = value.trim();
  if (!trimmed) {
    return '';
  }

  return trimmed.replace(/\/$/, '');
};

const rawBaseUrl = normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL);
const isAbsoluteUrl = /^https?:\/\//i.test(rawBaseUrl);
const relativeFallback = '/api';

const effectiveBaseUrl =
  (import.meta.env.DEV && isAbsoluteUrl ? relativeFallback : rawBaseUrl) || relativeFallback;

const buildUrl = (path: string) => {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${effectiveBaseUrl}${normalizedPath}`;
};

export const sendMessage = async (
  message: string,
  signal?: AbortSignal,
): Promise<SendMessageResponse> => {
  const payload: SendMessagePayload = { message };
  const response = await fetch(buildUrl('/chat'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(payload),
    signal,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || 'در برقراری ارتباط با سرور خطایی رخ داده است.');
  }

  const data = (await response.json()) as SendMessageResponse;
  if (!data || typeof data.reply !== 'string') {
    throw new Error('پاسخ نامعتبر از سرور دریافت شد.');
  }

  return data;
};
