import { useState, useEffect, useRef, memo } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Send, Bot, User, Loader2 } from 'lucide-react';
import { Card } from './ui/card';

// TradingView 위젯 컴포넌트
const TradingViewWidget = memo(({ symbol }: { symbol: string }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const container = containerRef.current;
    if (!container || !symbol) return;
    
    while (container.firstChild) {
      container.removeChild(container.firstChild);
    }

    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/tv.js';
    script.async = true;
    script.onload = () => {
      // @ts-ignore
      if (window.TradingView) {
        // @ts-ignore
        new window.TradingView.widget({
          "autosize": true,
          "symbol": symbol,
          "interval": "D",
          "timezone": "Etc/UTC",
          "theme": "dark",
          "style": "1",
          "locale": "kr",
          "enable_publishing": false,
          "allow_symbol_change": true,
          "container_id": container.id
        });
      }
    };
    
    container.id = `tradingview_widget_container_${symbol}_${Date.now()}`;
    container.appendChild(script);

  }, [symbol]);

  return <div ref={containerRef} style={{ height: '400px', width: '100%' }} />;
});


interface StockHolding {
  symbol: string; name: string; quantity: number; avgPrice: number; currentPrice: number;
}
interface WatchlistItem {
  symbol: string; name: string;
}
interface AIChatbotProps {
  stockHoldings: StockHolding[];
  watchlist: WatchlistItem[];
}
interface Message {
  id: string; 
  type: 'user' | 'bot'; 
  content: string;
  tradingViewSymbol?: string;
}

const suggestedQuestions = [
  '내 포트폴리오 수익률은?', '애플 주가는?', '알파벳 관련 최신 뉴스 찾아줘', '아마존 최신 리포트 요약해줘'
];

export function AIChatbot({ stockHoldings, watchlist }: AIChatbotProps) {
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', type: 'bot', content: '안녕하세요! AI Analyst입니다. 무엇이든 물어보세요.' }
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

    const userMessage: Message = { id: Date.now().toString(), type: 'user', content: message };
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const apiHistory = [...messages, userMessage] // 현재 질문까지 포함
        .filter(msg => msg.type === 'user' || msg.type === 'bot')
        .map(msg => ({ type: msg.type === 'user' ? 'human' : 'ai', content: msg.content }));

      const response = await fetch(`/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: message,
          user_stocks: stockHoldings,
          watchlist: watchlist,
          chat_history: apiHistory.slice(0, -1)
        }),
      });

      if (!response.ok) throw new Error('서버에서 오류가 발생했습니다.');
      const data = await response.json();
      
      const botMessage: Message = { 
        id: (Date.now() + 1).toString(), 
        type: 'bot', 
        content: data.answer || "답변을 생성하지 못했습니다.",
        tradingViewSymbol: data.tradingview_symbol || undefined
      };
      
      setMessages(prev => [...prev, botMessage]);

    } catch (error) {
        const errorMessage: Message = { id: (Date.now() + 1).toString(), type: 'bot', content: '죄송합니다. 오류가 발생했습니다.' };
        setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };



  return (
    <div className="flex flex-col h-full bg-background">
      <div ref={scrollAreaRef} className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div key={message.id} className={`flex items-start gap-2 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
            {message.type === 'bot' && <Bot className="w-6 h-6 text-primary flex-shrink-0" />}
            <div className={message.type === 'user' ? 'rounded-lg px-4 py-2 bg-primary text-primary-foreground max-w-[85%]' : 'w-full'}>
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
              {message.type === 'bot' && message.tradingViewSymbol && (
                <Card className="mt-2 p-0 overflow-hidden">
                  <TradingViewWidget symbol={message.tradingViewSymbol} />
                </Card>
              )}
            </div>
            {message.type === 'user' && <User className="w-6 h-6 flex-shrink-0" />}
          </div>
        ))}

        {/* AI 답변 로딩 인디케이터 */}
        {isLoading && (
          <div className="flex items-start gap-2 justify-start mt-4">
              <Bot className="w-6 h-6 text-primary flex-shrink-0" />
              <Loader2 className="w-6 h-6 animate-spin text-primary" />
          </div>
        )}
      </div>

      <div className={`p-4 border-t bg-background`}>
        <div className="flex flex-wrap gap-2 mb-2">
            {suggestedQuestions.map((q, i) => <Button key={i} variant="outline" size="sm" className="text-xs" onClick={() => handleSendMessage(q)} disabled={isLoading}>{q}</Button>)}
        </div>
        <form onSubmit={e => { e.preventDefault(); handleSendMessage(inputValue); }} className="flex gap-2">
          <Input value={inputValue} onChange={e => setInputValue(e.target.value)} placeholder="메시지를 입력하세요..." disabled={isLoading} />
          <Button type="submit" size="icon" disabled={isLoading || !inputValue.trim()}><Send className="w-4 h-4" /></Button>
        </form>
      </div>
    </div>
  );
}
