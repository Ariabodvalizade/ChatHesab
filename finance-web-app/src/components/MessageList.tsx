import { Avatar, Box, CircularProgress, Paper, Stack, Typography } from '@mui/material';
import SmartToyRoundedIcon from '@mui/icons-material/SmartToyRounded';
import PersonRoundedIcon from '@mui/icons-material/PersonRounded';
import { ChatMessage } from '../types/chat';

interface MessageListProps {
  messages: ChatMessage[];
  isLoading?: boolean;
}

const formatTime = (value: string) => {
  try {
    const formatter = new Intl.DateTimeFormat('fa-IR', {
      hour: '2-digit',
      minute: '2-digit',
    });

    return formatter.format(new Date(value));
  } catch (error) {
    return value;
  }
};

const MessageList = ({ messages, isLoading = false }: MessageListProps): JSX.Element => {
  return (
    <Stack spacing={2} sx={{ maxHeight: { xs: '60vh', md: '65vh' }, overflowY: 'auto', px: 1 }}>
      {messages.map((message) => {
        const isUser = message.role === 'user';

        return (
          <Box
            key={message.id}
            sx={{
              display: 'flex',
              flexDirection: isUser ? 'row-reverse' : 'row',
              alignItems: 'flex-start',
              gap: 2,
            }}
          >
            <Avatar sx={{ bgcolor: isUser ? 'primary.main' : 'secondary.main' }}>
              {isUser ? <PersonRoundedIcon /> : <SmartToyRoundedIcon />}
            </Avatar>

            <Paper
              elevation={0}
              sx={{
                p: 2,
                bgcolor: isUser ? 'primary.main' : 'background.paper',
                color: isUser ? 'primary.contrastText' : 'text.primary',
                borderRadius: 3,
                borderTopLeftRadius: isUser ? 3 : 0,
                borderTopRightRadius: isUser ? 0 : 3,
                minWidth: '40%',
              }}
            >
              <Typography variant="body1" sx={{ whiteSpace: 'pre-line' }}>
                {message.content}
              </Typography>
              <Typography variant="caption" sx={{ display: 'block', mt: 1, textAlign: 'left', opacity: 0.7 }}>
                {formatTime(message.createdAt)}
              </Typography>
            </Paper>
          </Box>
        );
      })}

      {isLoading && (
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 2,
          }}
        >
          <Avatar sx={{ bgcolor: 'secondary.main' }}>
            <SmartToyRoundedIcon />
          </Avatar>
          <Paper elevation={0} sx={{ p: 2, borderRadius: 3, minWidth: '40%' }}>
            <Stack direction="row" spacing={1} alignItems="center">
              <CircularProgress size={18} />
              <Typography variant="body2">در حال فکر کردن...</Typography>
            </Stack>
          </Paper>
        </Box>
      )}
    </Stack>
  );
};

export default MessageList;
