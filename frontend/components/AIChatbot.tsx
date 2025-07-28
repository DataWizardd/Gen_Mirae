import { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { ScrollArea } from './ui/scroll-area';
import { Send, Bot, User } from 'lucide-react';
import { useMobile } from './ui/use-mobile';

interface Message {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: Date;
  chart?: React.ReactNode;
}

const suggestedQuestions = [
  '내 포트폴리오 수익률은?',
  '애플 주가는?',
  '최근 시장 동향을 알려주세요',
  '엔비디아의 최근 증권사 리포트 요약해줘'
];

const mockResponses: { [key: string]: string } = {
  '포트폴리오': '현재 포트폴리오는 국내 주식 43.75%, 해외 주식 43.75%, 현금 12.5%로 구성되어 있습니다. 전체 수익률은 +6.07%로 양호한 성과를 보이고 있습니다.',
  '수익률': '현재 전체 포트폴리오 수익률은 +6.07%입니다. 해외 주식 부문에서 +6.71%의 좋은 성과를 보이고 있고, 국내 주식도 +5.43%로 안정적인 수익을 기록하고 있습니다.',
  '엔비디아': '엔비디아(NVDA)는 현재 $875 수준에서 거래되고 있습니다. AI 칩 수요 증가로 지난달 대비 +8.2% 상승했으며, 목표가는 $950-$1000 구간으로 예상됩니다.',
  '애플': '애플 최근 증권사 리포트 요약: 골드만삭스는 목표가 $250로 상향 조정했으며, 아이폰 16 Pro 판매량이 예상을 상회하고 있다고 분석했습니다. 서비스 부문 성장도 긍정적으로 평가받고 있습니다.',
  '시장': '최근 AI 관련 기업들의 실적 호조로 기술주가 상승세를 보이고 있습니다. 반도체 섹터 특히 강세를 보이고 있으며, 연말 랠리 기대감도 높아지고 있습니다.',
  '리포트': '애플 증권사 리포트 요약: 모건스탠리는 아이폰 매출 성장과 서비스 부문 확장을 근거로 매수 추천을 유지했습니다. 2024년 예상 EPS는 $7.8-$8.2 구간으로 전망됩니다.'
};

export function AIChatbot() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'bot',
      content: '안녕하세요! AI Analyst입니다. 궁금한 점이 있으시면 언제든 물어보세요.',
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const isMobile = useMobile();

  const generateResponse = (userMessage: string): string => {
    const lowercaseMessage = userMessage.toLowerCase();
    
    for (const [keyword, response] of Object.entries(mockResponses)) {
      if (lowercaseMessage.includes(keyword)) {
        return response;
      }
    }
    
    return '죄송합니다. 좀 더 구체적인 질문을 해주시면 더 정확한 답변을 드릴 수 있습니다. 포트폴리오, 수익률, 특정 종목, 시장 동향 등에 대해 물어보세요.';
  };

  const handleSendMessage = (message: string) => {
    if (!message.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: message,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');

    // 봇 응답 시뮬레이션
    setTimeout(() => {
      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: generateResponse(message),
        timestamp: new Date()
      };
      setMessages(prev => [...prev, botResponse]);
    }, 1000);
  };

  const handleSuggestedQuestion = (question: string) => {
    handleSendMessage(question);
  };

  return (
    <div className={`bg-card rounded-lg shadow-sm border flex flex-col ${
      isMobile ? 'h-[calc(100vh-200px)]' : 'h-96'
    }`}>
      <div className="p-4 border-b">
        <div className="flex items-center space-x-2">
          <Bot className="w-5 h-5 text-blue-600" />
          <h3>AI Advisor</h3>
        </div>
      </div>

      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] rounded-lg p-3 ${
                  message.type === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-foreground'
                }`}
              >
                <div className="flex items-start space-x-2">
                  {message.type === 'bot' && <Bot className="w-4 h-4 mt-0.5 text-blue-600" />}
                  <div className="flex-1">
                    <p className="text-sm leading-relaxed">{message.content}</p>
                    {message.chart && <div className="mt-2">{message.chart}</div>}
                  </div>
                  {message.type === 'user' && (
                    <User className={`w-4 h-4 mt-0.5 ${message.type === 'user' ? 'text-primary-foreground' : ''}`} />
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>

      <div className="p-4 border-t space-y-3">
        <div className="flex flex-wrap gap-2">
          {suggestedQuestions.map((question, index) => (
            <Button
              key={index}
              variant="outline"
              size="sm"
              onClick={() => handleSuggestedQuestion(question)}
              className={`${isMobile ? 'text-xs h-8 px-3' : 'text-xs h-7'}`}
            >
              {question}
            </Button>
          ))}
        </div>
        
        <div className="flex space-x-2">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="질문을 입력하세요..."
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage(inputValue)}
            className="flex-1"
          />
          <Button 
            onClick={() => handleSendMessage(inputValue)} 
            size="sm"
            className="h-10 px-3"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}