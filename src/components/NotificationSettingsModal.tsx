import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Bot, Send, User } from 'lucide-react';

interface NotificationSettingsModalProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
}

interface ChatMessage {
  type: 'bot' | 'user';
  text: string;
}

export function NotificationSettingsModal({ isOpen, onOpenChange }: NotificationSettingsModalProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { type: 'bot', text: '안녕하세요! 어떤 종류의 알림을 받고 싶으신가요? 특정 종목, 시장 이벤트, 또는 AI 추천 등 자유롭게 말씀해주세요.' }
  ]);
  const [inputValue, setInputValue] = useState('');

  const handleSendMessage = () => {
    if (!inputValue.trim()) return;
    const newMessages: ChatMessage[] = [...messages, { type: 'user', text: inputValue }];
    // Mock bot response
    newMessages.push({ type: 'bot', text: `알겠습니다. "${inputValue}" 관련 알림을 설정해 드릴게요. 또 다른 설정이 필요하신가요?` });
    setMessages(newMessages);
    setInputValue('');
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="w-[30vw] max-w-[70px] p-3">
        <DialogHeader>
          <DialogTitle className="text-sm">알림 설정</DialogTitle>
          <DialogDescription className="text-xs">
            원하는 알림을 요청해보세요.
          </DialogDescription>
        </DialogHeader>
        <div className="h-[150px] flex flex-col">
          <div className="flex-1 overflow-y-auto p-2 space-y-2 border rounded bg-muted/50">
            {messages.map((msg, index) => (
              <div key={index} className={`flex items-start gap-1 ${msg.type === 'user' ? 'justify-end' : ''}`}>
                {msg.type === 'bot' && <Bot className="w-3 h-3 text-primary flex-shrink-0" />}
                <div className={`p-2 rounded max-w-[75%] ${msg.type === 'bot' ? 'bg-background' : 'bg-primary text-primary-foreground'}`}>
                  <p className="text-xs leading-tight">{msg.text}</p>
                </div>
                {msg.type === 'user' && <User className="w-3 h-3 text-primary flex-shrink-0" />}
              </div>
            ))}
          </div>
          <div className="mt-2 flex gap-1">
            <Input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="예: MSFT 주가"
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              className="text-xs h-7"
            />
            <Button onClick={handleSendMessage} size="sm" className="h-7 px-2">
              <Send className="w-3 h-3" />
            </Button>
          </div>
        </div>
        <DialogFooter>
          <Button onClick={() => onOpenChange(false)} className="text-xs h-7 w-full">완료</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
} 