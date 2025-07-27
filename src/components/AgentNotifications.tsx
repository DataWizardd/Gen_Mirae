import { Card } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
// import { ScrollArea } from './ui/scroll-area';
import { 
  TrendingUp, 
  TrendingDown, 
  Newspaper, 
  Calendar,
  AlertTriangle,
  CheckCircle,
  X,
  Bell,
  Settings
} from 'lucide-react';
import { useState } from 'react';
import { NotificationSettingsModal } from './NotificationSettingsModal';
// import { useMobile } from './ui/use-mobile';

interface Notification {
  id: string;
  type: 'urgent' | 'info' | 'earnings' | 'news';
  title: string;
  content: string;
  asset: string;
  change?: number;
  changePercent?: number;
  timestamp: string;
  isRead: boolean;
}

const mockNotifications: Notification[] = [
  {
    id: '1',
    type: 'urgent',
    title: '엔비디아 실적 발표',
    content: 'AI 칩 수요 증가로 시장 예상치를 상회하는 실적을 발표했습니다.',
    asset: '엔비디아',
    change: 48.00,
    changePercent: 8.5,
    timestamp: '방금 전',
    isRead: false
  },
  {
    id: '2',
    type: 'earnings',
    title: 'AAPL 어닝콜 예정',
    content: '애플 Q4 실적 발표 예정 (한국시간 새벽 5시). 아이폰 매출 주목',
    asset: 'AAPL',
    timestamp: '1시간 전',
    isRead: false
  },
  {
    id: '3',
    type: 'news',
    title: 'NVDA 관련 뉴스',
    content: '엔비디아 새로운 AI 칩 공개. 전 세계 데이터센터 수요 급증 예상',
    asset: 'NVDA',
    timestamp: '2시간 전',
    isRead: true
  },
  {
    id: '4',
    type: 'info',
    title: '포트폴리오 리밸런싱 제안',
    content: '해외 주식 비중이 높습니다. 국내 주식으로 일부 분산 투자를 고려해보세요.',
    asset: '전체',
    timestamp: '3시간 전',
    isRead: true
  }
];

const getNotificationIcon = (type: string) => {
  switch (type) {
    case 'urgent':
      return <AlertTriangle className="w-4 h-4 text-red-500" />;
    case 'earnings':
      return <Calendar className="w-4 h-4 text-blue-500" />;
    case 'news':
      return <Newspaper className="w-4 h-4 text-green-500" />;
    default:
      return <Bell className="w-4 h-4 text-yellow-500" />;
  }
};

const getNotificationBadge = (type: string) => {
  switch (type) {
    case 'urgent':
      return <Badge variant="destructive" className="text-xs">긴급</Badge>;
    case 'earnings':
      return <Badge variant="default" className="text-xs bg-blue-500">실적</Badge>;
    case 'news':
      return <Badge variant="secondary" className="text-xs">뉴스</Badge>;
    default:
      return <Badge variant="outline" className="text-xs">정보</Badge>;
  }
};

export function AgentNotifications() {
  const [notifications, setNotifications] = useState(mockNotifications);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
  // const isMobile = useMobile();
  
  const unreadCount = notifications.filter(n => !n.isRead).length;
  const displayNotifications = isExpanded ? notifications : notifications.slice(0, 2);

  const markAsRead = (id: string) => {
    setNotifications(prev => 
      prev.map(notification => 
        notification.id === id 
          ? { ...notification, isRead: true }
          : notification
      )
    );
  };

  const dismissNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  return (
    <Card className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950/50 dark:to-purple-950/50 border-blue-200 dark:border-blue-800">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-full">
            <Bell className="w-4 h-4 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h3 className="font-medium">AI 애널리스트 알림</h3>
            <p className="text-xs text-muted-foreground">
              {unreadCount > 0 ? `${unreadCount}개의 새로운 알림` : '모든 알림을 확인했습니다'}
            </p>
          </div>
        </div>
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setIsSettingsModalOpen(true)}>
          <Settings className="h-4 w-4" />
        </Button>
        {unreadCount > 0 && (
          <Badge variant="destructive" className="text-xs">
            {unreadCount}
          </Badge>
        )}
      </div>

      <div className="space-y-3">
        {displayNotifications.map((notification) => (
          <div
            key={notification.id}
            className={`p-3 rounded-lg border transition-all ${
              notification.isRead 
                ? 'bg-muted/30 border-border/50' 
                : 'bg-card border-blue-200 dark:border-blue-800 shadow-sm'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-2 flex-1">
                {getNotificationIcon(notification.type)}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <h4 className={`text-sm ${!notification.isRead ? 'font-medium' : ''}`}>
                      {notification.title}
                    </h4>
                    {getNotificationBadge(notification.type)}
                  </div>
                  <p className="text-xs text-muted-foreground mb-2 line-clamp-2">
                    {notification.content}
                  </p>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                      <span>{notification.asset}</span>
                      <span>•</span>
                      <span>{notification.timestamp}</span>
                    </div>
                    {notification.change && (
                      <div className={`flex items-center space-x-1 text-xs ${
                        notification.changePercent! > 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {notification.changePercent! > 0 ? (
                          <TrendingUp className="w-3 h-3" />
                        ) : (
                          <TrendingDown className="w-3 h-3" />
                        )}
                        <span>
                          {notification.changePercent! > 0 ? '+' : ''}{notification.changePercent}%
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex items-start space-x-1 ml-2">
                {!notification.isRead && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => markAsRead(notification.id)}
                    className="h-6 w-6 p-0 hover:bg-blue-100 dark:hover:bg-blue-900"
                  >
                    <CheckCircle className="w-3 h-3" />
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => dismissNotification(notification.id)}
                  className="h-6 w-6 p-0 hover:bg-red-100 dark:hover:bg-red-900"
                >
                  <X className="w-3 h-3" />
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {notifications.length > 2 && (
        <div className="mt-3 text-center">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-xs"
          >
            {isExpanded ? '접기' : `${notifications.length - 2}개 더 보기`}
          </Button>
        </div>
      )}

      <NotificationSettingsModal 
        isOpen={isSettingsModalOpen}
        onOpenChange={setIsSettingsModalOpen}
      />
    </Card>
  );
}