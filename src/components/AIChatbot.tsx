import { useState, useEffect, useRef, memo } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Send, Bot, User, Loader2 } from 'lucide-react';

const TradingViewWidget = memo(({ htmlContent }: { htmlContent: string }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const container = containerRef.current;
    if (!container || !htmlContent) return;

    while (container.firstChild) {
      container.removeChild(container.firstChild);
    }
    
    const template = document.createElement('template');
    template.innerHTML = htmlContent.trim();
    const content = template.content;

    const scriptTag = content.querySelector<HTMLScriptElement>('script[src="https://s3.tradingview.com/tv.js"]');
    const inlineScriptTag = Array.from(content.querySelectorAll<HTMLScriptElement>('script')).find(s => !s.src);
    
    const widgetContainer = content.querySelector('.tradingview-widget-container');
    if (widgetContainer) {
      container.appendChild(widgetContainer);
    }

    if (scriptTag && inlineScriptTag) {
      const newScript = document.createElement('script');
      newScript.src = scriptTag.src;
      newScript.async = true;
      newScript.onload = () => {
        const newInlineScript = document.createElement('script');
        newInlineScript.innerHTML = inlineScriptTag.innerHTML;
        container.appendChild(newInlineScript);
      };
      document.body.appendChild(newScript);

      return () => {
        if (document.body.contains(newScript)) {
          document.body.removeChild(newScript);
        }
      };
    }
  }, [htmlContent]);

  return <div ref={containerRef} />;
});

interface StockHolding {
  symbol: string;
  name: string;
  quantity: number;
  avgPrice: number;
  currentPrice: number;
}

interface WatchlistItem {
  symbol: string;
  name: string;
}

interface AIChatbotProps {
  stockHoldings: StockHolding[];
  watchlist: WatchlistItem[];
}

interface Message {
  id: string;
  type: 'user' | 'bot' | 'chart'; // chart 타입 추가
  content: string;
  timestamp: Date;
}

const suggestedQuestions = [
  '내 포트폴리오 수익률은?',
  '애플 주가는?',
  '알파벳과 관련된 최근 기사를 찾아주세요',
  '아마존의 최근 증권사 리포트 요약해줘'
];

export function AIChatbot({ stockHoldings, watchlist }: AIChatbotProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'bot',
      content: '안녕하세요! AI Analyst입니다. 궁금한 점이 있으시면 언제든 물어보세요.',
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async (message: string) => {
    if (!message.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: message,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const apiUrl = process.env.REACT_APP_API_URL || '';
      const response = await fetch(`${apiUrl}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: message,
          user_stocks: stockHoldings.map(s => ({
            "티커": s.symbol,
            "종목명": s.name,
            "수량": s.quantity,
            "평균단가": s.avgPrice,
            "현재가": s.currentPrice
          })),
          watchlist: watchlist.map(w => ({ "symbol": w.symbol, "name": w.name }))
        }),
      });

      if (!response.ok) throw new Error('Network response was not ok');
      const data = await response.json();
      
      const newMessages: Message[] = [];
      
      // LLM 답변 메시지
      newMessages.push({
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: data.answer,
        timestamp: new Date(),
      });
      
      // TradingView 차트가 있으면 별도의 메시지로 추가
      if (data.tradingview_html) {
        newMessages.push({
          id: (Date.now() + 2).toString(),
          type: 'chart',
          content: data.tradingview_html,
          timestamp: new Date(),
        });
      }

      setMessages(prev => [...prev, ...newMessages]);

    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: '죄송합니다. 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleSuggestedQuestion = (question: string) => handleSendMessage(question);

  return (
    <div className="flex flex-col h-full w-full bg-background text-foreground">
      {/* Messages Area */}
      <div ref={scrollAreaRef} className="flex-1 overflow-y-auto p-3 space-y-4">
        {messages.map((message) => {
          if (message.type === 'user') {
            return (
              <div key={message.id} className="flex justify-end">
                <div className="max-w-[85%] rounded-lg p-3 bg-primary text-primary-foreground">
                  <div className="flex items-start gap-2">
                    <p className="text-sm leading-relaxed">{message.content}</p>
                    <User className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  </div>
                </div>
              </div>
            );
          }
          if (message.type === 'bot') {
            return (
              <div key={message.id} className="flex justify-start">
                <div className="w-full">
                  <div className="flex items-start gap-2">
                    <Bot className="w-5 h-5 mt-0.5 text-blue-600 flex-shrink-0" />
                    <p className="text-sm leading-relaxed whitespace-pre-wrap pt-0.5">{message.content}</p>
                  </div>
                </div>
              </div>
            );
          }
          if (message.type === 'chart') {
            return (
              <div key={message.id} className="w-full h-[350px] bg-card rounded-lg overflow-hidden border">
                <TradingViewWidget htmlContent={message.content} />
              </div>
            );
          }
          return null;
        })}
        {isLoading && (
          <div className="flex justify-start">
             <div className="flex items-start gap-2">
                <Bot className="w-5 h-5 mt-0.5 text-blue-600 flex-shrink-0" />
                <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
             </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="flex-shrink-0 p-3 border-t border-border bg-card">
        <div className="space-y-2">
          {/* 추천 질문 리스트 */}
          <div className="flex flex-wrap gap-1">
            {suggestedQuestions.map((question, index) => (
              <Button
                key={index}
                variant="outline"
                size="sm"
                onClick={() => handleSuggestedQuestion(question)}
                className="text-xs h-7 px-2 text-muted-foreground hover:text-foreground"
              >
                {question}
              </Button>
            ))}
          </div>
          {/* Input form */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage(inputValue);
            }}
            className="flex items-center gap-2"
          >
            <Input
              type="text"
              placeholder="메시지를 입력하세요..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              className="flex-1"
              disabled={isLoading}
            />
            <Button type="submit" size="icon" disabled={isLoading}>
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}