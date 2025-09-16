import { FormEvent, useState } from 'react';
import { IconButton, InputAdornment, Paper, TextField } from '@mui/material';
import SendRoundedIcon from '@mui/icons-material/SendRounded';

interface MessageInputProps {
  onSend: (message: string) => Promise<void> | void;
  disabled?: boolean;
}

const MessageInput = ({ onSend, disabled = false }: MessageInputProps): JSX.Element => {
  const [value, setValue] = useState('');

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = value.trim();

    if (!trimmed) {
      return;
    }

    try {
      await onSend(trimmed);
      setValue('');
    } catch (error) {
      // خطا در سطح بالاتر مدیریت می‌شود.
    }
  };

  return (
    <Paper component="form" elevation={3} onSubmit={handleSubmit} sx={{ p: 2, mt: 3 }}>
      <TextField
        fullWidth
        multiline
        minRows={1}
        maxRows={4}
        disabled={disabled}
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder="پیام خود را بنویسید..."
        InputProps={{
          endAdornment: (
            <InputAdornment position="end">
              <IconButton type="submit" color="primary" disabled={disabled || !value.trim()}>
                <SendRoundedIcon />
              </IconButton>
            </InputAdornment>
          ),
        }}
      />
    </Paper>
  );
};

export default MessageInput;
