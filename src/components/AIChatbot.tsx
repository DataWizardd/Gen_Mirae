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
    const oldScripts = document.querySelectorAll(`script[data-widget-id^="tradingview_widget"]`);
    oldScripts.forEach(s => s.remove());

    const template = document.createElement('template');
    template.innerHTML = htmlContent.trim();
    const content = template.content;
    
    const widgetContainer = content.querySelector('.tradingview-widget-container');
    if (widgetContainer) {
      container.appendChild(widgetContainer);
    }
    
    const scriptTag = content.querySelector<HTMLScriptElement>('script[src="https://s3.tradingview.com/tv.js"]');
    if (scriptTag) {
      const newScript = document.createElement('script');
      newScript.src = scriptTag.src;
      newScript.async = true;
      newScript.setAttribute('data-widget-id', `tradingview_widget_${Date.now()}`);
      newScript.onload = () => {
        const inlineScriptContent = content.querySelector('script:not([src])')?.innerHTML;
        if(inlineScriptContent) {
            const newInlineScript = document.createElement('script');
            newInlineScript.innerHTML = inlineScriptContent;
            container.appendChild(newInlineScript);
        }
      };
      document.body.appendChild(newScript);
    }
  }, [htmlContent]);

  return <div ref={containerRef} />;
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
  id: string; type: 'user' | 'bot' | 'chart'; content: string;
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
    const currentMessages = [...messages, userMessage];
    setMessages(currentMessages);
    setInputValue('');
    setIsLoading(true);

    try {
      const apiHistory = currentMessages
        .filter(msg => msg.type === 'user' || msg.type === 'bot')
        .map(msg => ({ type: msg.type === 'user' ? 'human' : 'ai', content: msg.content }));

      const response = await fetch(`/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: message,
          user_stocks: stockHoldings.map(s => ({ "티커": s.symbol, "종목명": s.name, "수량": s.quantity, "평균단가": s.avgPrice, "현재가": s.currentPrice })),
          watchlist: watchlist.map(w => ({ "symbol": w.symbol, "name": w.name })),
          chat_history: apiHistory.slice(0, -1)
        }),
      });

      if (!response.ok) throw new Error('서버에서 오류가 발생했습니다.');
      const data = await response.json();
      
      const newMessages: Message[] = [];
      if (data.answer) {
        newMessages.push({ id: (Date.now() + 1).toString(), type: 'bot', content: data.answer });
      }
      if (data.tradingview_html) {
        newMessages.push({ id: (Date.now() + 2).toString(), type: 'chart', content: data.tradingview_html });
      }
      setMessages(prev => [...prev, ...newMessages]);

    } catch (error) {
      setMessages(prev => [...prev, { id: (Date.now() + 1).toString(), type: 'bot', content: '죄송합니다. 오류가 발생했습니다.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-background">
      <div ref={scrollAreaRef} className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div key={message.id} className={`flex items-end gap-2 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
            {message.type === 'bot' && <Bot className="w-6 h-6 text-primary flex-shrink-0" />}
            <div className={message.type === 'user' ? 'rounded-lg px-4 py-2 bg-primary text-primary-foreground max-w-[85%]' : 'w-full'}>
              {message.type === 'chart' ? <TradingViewWidget htmlContent={message.content} /> : <p className="text-sm whitespace-pre-wrap">{message.content}</p>}
            </div>
            {message.type === 'user' && <User className="w-6 h-6 flex-shrink-0" />}
          </div>
        ))}
        {isLoading && <div className="flex justify-start"><Bot className="w-6 h-6 text-primary flex-shrink-0" /><Loader2 className="w-6 h-6 ml-2 animate-spin" /></div>}
      </div>
      <div className={`p-4 border-t bg-background transition-opacity ${isLoading ? 'opacity-50 pointer-events-none' : 'opacity-100'}`}>
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
