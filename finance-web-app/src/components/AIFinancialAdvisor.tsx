// src/components/AIFinancialAdvisor.tsx
import React, { useState, useEffect, useRef } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  TextField,
  Alert,
  Card,
  CardContent,
  Avatar,
  Chip,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Psychology,
  TrendingUp,
  TrendingDown,
  AttachMoney,
  Timeline,
  ExpandMore,
  Send,
  AccessTime,
  CheckCircle,
  Cancel,
  Warning,
  Lightbulb,
  Analytics,
  AccountBalance,
  Security,
  Info,
  Savings,
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import { API_CONFIG, getAuthHeaders } from '../config/api';

interface AnalysisResult {
  is_valid_financial_question: boolean;
  response_message: string;
  analysis: {
    financial_health_score: number;
    strengths: string[];
    weaknesses: string[];
    recommendations: string[];
    investment_suggestions: string[];
    cost_optimization: string[];
    risk_warnings: string[];
  };
  spending_analysis: {
    top_categories: {
      [category: string]: {
        amount: number;
        percentage: number;
        trend: 'increasing' | 'decreasing' | 'stable';
      };
    };
  };
  usage_info?: {
    usage_remaining: number;
    next_available_minutes: number;
  };
}

interface UsageLimit {
  can_use: boolean;
  usage_count: number;
  limit: number;
  minutes_remaining: number;
}

export default function AIFinancialAdvisor() {
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<{ id: string; text: string; sender: 'user' | 'bot' }[]>([
    { id: 'intro', text: 'سلام، هر سوال مالی داری بپرس.', sender: 'bot' },
  ]);
  const [usageLimit, setUsageLimit] = useState<UsageLimit | null>(null);
  const [error, setError] = useState('');
  const [guidelinesOpen, setGuidelinesOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    checkUsageLimit();
  }, []);

  const checkUsageLimit = async () => {
    if (!token) return;

    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.AI_ADVISOR_USAGE}`, {
        headers: getAuthHeaders(token),
      });

      if (response.ok) {
        const data = await response.json();
        setUsageLimit(data);
      }
    } catch (error) {
      console.error('Error checking usage limit:', error);
    }
  };

  const performAnalysis = async () => {
    if (!token || !usageLimit?.can_use) return;

    setLoading(true);
    setError('');

    try {
      // Push user message to conversation
      setMessages((prev) => [...prev, { id: Date.now().toString(), text: question.trim(), sender: 'user' }]);

      const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.AI_ADVISOR_ANALYZE}`, {
        method: 'POST',
        headers: getAuthHeaders(token),
        body: JSON.stringify({
          question: question || 'لطفاً وضعیت مالی من را تحلیل کنید',
          analysis_type: 'comprehensive'
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setAnalysisResult(data);
          setQuestion('');
          setMessages((prev) => [...prev, { id: (Date.now()+1).toString(), text: data.response_message, sender: 'bot' }]);
          await checkUsageLimit(); // Update usage limit
        } else {
          setError(data.message || data.error || 'خطا در تحلیل وضعیت مالی');
        }
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'خطا در تحلیل وضعیت مالی');
      }
    } catch (error) {
      console.error('Error performing analysis:', error);
      setError('خطا در اتصال به سرور');
    } finally {
      setLoading(false);
    }
  };

  const getHealthScoreColor = (score: number) => {
    if (score >= 80) return 'success';
    if (score >= 60) return 'warning';
    return 'error';
  };

  const getHealthScoreText = (score: number) => {
    if (score >= 80) return 'عالی';
    if (score >= 60) return 'متوسط';
    return 'نیاز به بهبود';
  };

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('fa-IR').format(amount);
  };

  const formatTimeRemaining = (minutesRemaining: number) => {
    if (minutesRemaining <= 0) return 'قابل استفاده';
    
    if (minutesRemaining < 60) return `${minutesRemaining} دقیقه`;
    
    const hours = Math.ceil(minutesRemaining / 60);
    return `${hours} ساعت`;
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box display="flex" alignItems="center">
          <Avatar sx={{ 
            bgcolor: 'primary.main', 
            mr: 2, 
            width: 64, 
            height: 64,
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
          }}>
            <Psychology sx={{ fontSize: 32 }} />
          </Avatar>
          <Box>
            <Typography variant="h4" component="h1" sx={{ 
              fontWeight: 'bold',
              background: 'linear-gradient(45deg, #667eea 30%, #764ba2 90%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>
              🧠 مشاوره هوشمند مالی
            </Typography>
            <Typography variant="subtitle1" color="text.secondary">
              تحلیل جامع وضعیت مالی با هوش مصنوعی Gemini 2.5 Pro
            </Typography>
          </Box>
        </Box>
        
        <Button
          variant="outlined"
          startIcon={<Info />}
          onClick={() => setGuidelinesOpen(true)}
          sx={{ borderRadius: 3 }}
        >
          راهنما و قوانین
        </Button>
      </Box>

      {/* Usage Status */}
      {usageLimit && (
        <Card sx={{ mb: 3, borderLeft: 4, borderLeftColor: usageLimit.can_use ? 'success.main' : 'warning.main' }}>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Box display="flex" alignItems="center">
                <AccessTime sx={{ mr: 2, color: usageLimit.can_use ? 'success.main' : 'warning.main' }} />
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                    وضعیت استفاده از مشاوره هوشمند
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    محدودیت: ۱ بار در هر ساعت
                  </Typography>
                </Box>
              </Box>
              
              <Box textAlign="right">
                {usageLimit.can_use ? (
                  <Chip
                    icon={<CheckCircle />}
                    label="قابل استفاده"
                    color="success"
                    variant="outlined"
                  />
                ) : (
                  <Chip
                    icon={<AccessTime />}
                    label={`باقی‌مانده: ${formatTimeRemaining(usageLimit.minutes_remaining)}`}
                    color="warning"
                    variant="outlined"
                  />
                )}
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Chat-like Advisor */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ minHeight: '40vh', maxHeight: '60vh', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 1 }}>
          {messages.map((m) => (
            <Box key={m.id} sx={{ display: 'flex', justifyContent: m.sender === 'user' ? 'flex-end' : 'flex-start' }}>
              <Box sx={{
                bgcolor: m.sender === 'user' ? 'primary.main' : 'grey.100',
                color: m.sender === 'user' ? 'white' : 'text.primary',
                px: 1.5, py: 1, borderRadius: 3, maxWidth: '80%'
              }}>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>{m.text}</Typography>
              </Box>
            </Box>
          ))}
        </Box>
        <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
          <TextField fullWidth size="small" placeholder="سوال مالی خود را بنویسید..." value={question} onChange={(e) => setQuestion(e.target.value)} />
          <Button variant="contained" onClick={performAnalysis} disabled={loading || !usageLimit?.can_use}>{loading ? '...' : 'ارسال'}</Button>
        </Box>
      </Paper>

      {/* Analysis Results (optional extra details) */}
      {analysisResult && (
        <>
          <Card sx={{ mb: 4, borderRadius: 3, background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)' }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
                🤖 نتیجه تحلیل هوشمند
              </Typography>
              <Typography variant="body1" sx={{ lineHeight: 1.8 }}>
                {analysisResult.response_message}
              </Typography>
            </CardContent>
          </Card>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {/* Financial Health Score Row */}
            <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
              {/* Financial Health Score */}
              <Box sx={{ flex: '1 1 300px', minWidth: '300px' }}>
                <Card sx={{
                  background: `linear-gradient(135deg, ${
                    analysisResult.analysis.financial_health_score >= 80 ? '#4CAF50' :
                    analysisResult.analysis.financial_health_score >= 60 ? '#FF9800' : '#f44336'
                  } 0%, ${
                    analysisResult.analysis.financial_health_score >= 80 ? '#81C784' :
                    analysisResult.analysis.financial_health_score >= 60 ? '#FFB74D' : '#ef5350'
                  } 100%)`,
                  color: 'white',
                  borderRadius: 3
                }}>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <Typography variant="h3" sx={{ fontWeight: 'bold', mb: 1 }}>
                      {analysisResult.analysis.financial_health_score}
                    </Typography>
                    <Typography variant="h6" sx={{ opacity: 0.9, mb: 2 }}>
                      امتیاز سلامت مالی
                    </Typography>
                    <Chip
                      label={getHealthScoreText(analysisResult.analysis.financial_health_score)}
                      sx={{ 
                        bgcolor: 'rgba(255,255,255,0.2)', 
                        color: 'white',
                        fontWeight: 'bold'
                      }}
                    />
                  </CardContent>
                </Card>
              </Box>

              {/* Strengths */}
              <Box sx={{ flex: '1 1 300px', minWidth: '300px' }}>
                <Card sx={{ height: '100%', borderRadius: 3 }}>
                  <CardContent>
                    <Box display="flex" alignItems="center" mb={2}>
                      <CheckCircle sx={{ mr: 2, color: 'success.main' }} />
                      <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                        ✅ نقاط قوت
                      </Typography>
                    </Box>
                    <List dense>
                      {analysisResult.analysis.strengths.map((strength, index) => (
                        <ListItem key={index} sx={{ pl: 0 }}>
                          <ListItemIcon sx={{ minWidth: 32 }}>
                            <CheckCircle color="success" fontSize="small" />
                          </ListItemIcon>
                          <ListItemText primary={strength} />
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              </Box>

              {/* Weaknesses */}
              <Box sx={{ flex: '1 1 300px', minWidth: '300px' }}>
                <Card sx={{ height: '100%', borderRadius: 3 }}>
                  <CardContent>
                    <Box display="flex" alignItems="center" mb={2}>
                      <Warning sx={{ mr: 2, color: 'warning.main' }} />
                      <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                        ⚠️ نقاط ضعف
                      </Typography>
                    </Box>
                    <List dense>
                      {analysisResult.analysis.weaknesses.map((weakness, index) => (
                        <ListItem key={index} sx={{ pl: 0 }}>
                          <ListItemIcon sx={{ minWidth: 32 }}>
                            <Warning color="warning" fontSize="small" />
                          </ListItemIcon>
                          <ListItemText primary={weakness} />
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              </Box>
            </Box>

            {/* Recommendations and Investment Row */}
            <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
              {/* Recommendations */}
              <Box sx={{ flex: '1 1 400px', minWidth: '400px' }}>
                <Accordion defaultExpanded>
                  <AccordionSummary expandIcon={<ExpandMore />} sx={{ bgcolor: 'primary.50' }}>
                    <Box display="flex" alignItems="center">
                      <Lightbulb sx={{ mr: 2, color: 'primary.main' }} />
                      <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                        💡 توصیه‌های بهینه‌سازی
                      </Typography>
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List>
                      {analysisResult.analysis.recommendations.map((rec, index) => (
                        <ListItem key={index}>
                          <ListItemIcon>
                            <CheckCircle color="success" />
                          </ListItemIcon>
                          <ListItemText primary={rec} />
                        </ListItem>
                      ))}
                    </List>
                  </AccordionDetails>
                </Accordion>
              </Box>

              {/* Investment Suggestions */}
              <Box sx={{ flex: '1 1 400px', minWidth: '400px' }}>
                <Accordion defaultExpanded>
                  <AccordionSummary expandIcon={<ExpandMore />} sx={{ bgcolor: 'success.50' }}>
                    <Box display="flex" alignItems="center">
                      <TrendingUp sx={{ mr: 2, color: 'success.main' }} />
                      <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                        📈 پیشنهادهای سرمایه‌گذاری
                      </Typography>
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List>
                      {analysisResult.analysis.investment_suggestions.map((suggestion, index) => (
                        <ListItem key={index}>
                          <ListItemIcon>
                            <AttachMoney color="success" />
                          </ListItemIcon>
                          <ListItemText primary={suggestion} />
                        </ListItem>
                      ))}
                    </List>
                  </AccordionDetails>
                </Accordion>
              </Box>
            </Box>

            {/* Cost Optimization and Risk Row */}
            <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
              {/* Cost Optimization */}
              <Box sx={{ flex: '1 1 400px', minWidth: '400px' }}>
                <Accordion defaultExpanded>
                  <AccordionSummary expandIcon={<ExpandMore />} sx={{ bgcolor: 'info.50' }}>
                    <Box display="flex" alignItems="center">
                      <Savings sx={{ mr: 2, color: 'info.main' }} />
                      <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                        💰 راه‌های کاهش هزینه
                      </Typography>
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List>
                      {analysisResult.analysis.cost_optimization.map((optimization, index) => (
                        <ListItem key={index}>
                          <ListItemIcon>
                            <Savings color="info" />
                          </ListItemIcon>
                          <ListItemText primary={optimization} />
                        </ListItem>
                      ))}
                    </List>
                  </AccordionDetails>
                </Accordion>
              </Box>

              {/* Risk Warnings */}
              {analysisResult.analysis.risk_warnings.length > 0 && (
                <Box sx={{ flex: '1 1 400px', minWidth: '400px' }}>
                  <Accordion defaultExpanded>
                    <AccordionSummary expandIcon={<ExpandMore />} sx={{ bgcolor: 'error.50' }}>
                      <Box display="flex" alignItems="center">
                        <Warning sx={{ mr: 2, color: 'error.main' }} />
                        <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                          🚨 هشدارهای مخاطرات مالی
                        </Typography>
                      </Box>
                    </AccordionSummary>
                    <AccordionDetails>
                      <List>
                        {analysisResult.analysis.risk_warnings.map((warning, index) => (
                          <ListItem key={index}>
                            <ListItemIcon>
                              <Warning color="error" />
                            </ListItemIcon>
                            <ListItemText primary={warning} />
                          </ListItem>
                        ))}
                      </List>
                    </AccordionDetails>
                  </Accordion>
                </Box>
              )}
            </Box>

            {/* Spending Analysis */}
            {analysisResult.spending_analysis?.top_categories && Object.keys(analysisResult.spending_analysis.top_categories).length > 0 && (
              <Box>
                <Card sx={{ borderRadius: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
                      📊 تحلیل تفصیلی هزینه‌ها
                    </Typography>
                    
                    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                      {Object.entries(analysisResult.spending_analysis.top_categories).map(([category, data]) => (
                        <Box key={category} sx={{ flex: '1 1 280px', minWidth: '280px' }}>
                          <Card variant="outlined" sx={{ p: 2 }}>
                            <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                              <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                                {category}
                              </Typography>
                              <Chip
                                size="small"
                                label={`${data.percentage.toFixed(1)}%`}
                                color={data.trend === 'increasing' ? 'error' : data.trend === 'decreasing' ? 'success' : 'default'}
                              />
                            </Box>
                            
                            <Typography variant="h6" color="primary.main" sx={{ mb: 1 }}>
                              {formatAmount(data.amount)} تومان
                            </Typography>
                            
                            <LinearProgress
                              variant="determinate"
                              value={data.percentage}
                              sx={{ height: 8, borderRadius: 1 }}
                            />
                          </Card>
                        </Box>
                      ))}
                    </Box>
                  </CardContent>
                </Card>
              </Box>
            )}
          </Box>
        </>
      )}

      {/* Guidelines Dialog */}
      <Dialog
        open={guidelinesOpen}
        onClose={() => setGuidelinesOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{
          background: 'linear-gradient(45deg, #667eea 30%, #764ba2 90%)',
          color: 'white',
          textAlign: 'center'
        }}>
          🧠 راهنما و قوانین مشاوره هوشمند مالی
        </DialogTitle>
        
        <DialogContent sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold', color: 'primary.main' }}>
            ✨ قابلیت‌های سیستم:
          </Typography>
          <List>
            <ListItem>
              <ListItemIcon><CheckCircle color="success" /></ListItemIcon>
              <ListItemText primary="تحلیل جامع تراکنش‌ها و الگوهای مالی" />
            </ListItem>
            <ListItem>
              <ListItemIcon><CheckCircle color="success" /></ListItemIcon>
              <ListItemText primary="ارائه توصیه‌های بهینه‌سازی هزینه‌ها" />
            </ListItem>
            <ListItem>
              <ListItemIcon><CheckCircle color="success" /></ListItemIcon>
              <ListItemText primary="پیشنهاد برنامه‌های سرمایه‌گذاری علمی" />
            </ListItem>
            <ListItem>
              <ListItemIcon><CheckCircle color="success" /></ListItemIcon>
              <ListItemText primary="محاسبه امتیاز سلامت مالی" />
            </ListItem>
            <ListItem>
              <ListItemIcon><CheckCircle color="success" /></ListItemIcon>
              <ListItemText primary="پاسخ به سوالات مالی تخصصی" />
            </ListItem>
          </List>

          <Divider sx={{ my: 3 }} />

          <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold', color: 'warning.main' }}>
            ⚠️ محدودیت‌ها و قوانین:
          </Typography>
          <List>
            <ListItem>
              <ListItemIcon><Warning color="warning" /></ListItemIcon>
              <ListItemText primary="هر کاربر تنها ۱ بار در ساعت می‌تواند از این سرویس استفاده کند" />
            </ListItem>
            <ListItem>
              <ListItemIcon><Cancel color="error" /></ListItemIcon>
              <ListItemText primary="احوال‌پرسی و گفتگوهای غیرمرتبط مجاز نیست" />
            </ListItem>
            <ListItem>
              <ListItemIcon><Cancel color="error" /></ListItemIcon>
              <ListItemText primary="پرسش درباره آمار سایر کاربران ممنوع است" />
            </ListItem>
            <ListItem>
              <ListItemIcon><Cancel color="error" /></ListItemIcon>
              <ListItemText primary="سوال درباره نحوه عملکرد سیستم مجاز نیست" />
            </ListItem>
            <ListItem>
              <Security color="info" />
              <ListItemText primary="تمام تحلیل‌ها بر اساس داده‌های شخصی شما و کاملاً محرمانه است" />
            </ListItem>
          </List>

          <Divider sx={{ my: 3 }} />

          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="body2">
              <strong>نکته مهم:</strong> این سیستم بر اساس هوش مصنوعی Gemini 2.5 Pro کار می‌کند و 
              توصیه‌های ارائه شده جنبه مشاورهای دارد. برای تصمیمات مالی مهم، حتماً با مشاور مالی متخصص مشورت کنید.
            </Typography>
          </Alert>
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setGuidelinesOpen(false)} variant="contained" sx={{ borderRadius: 2 }}>
            متوجه شدم
          </Button>
        </DialogActions>
      </Dialog>

      <div ref={messagesEndRef} />
    </Container>
  );
}
