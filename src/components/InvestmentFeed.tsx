import { Card } from './ui/card';
import { Button } from './ui/button';
import { Newspaper, Flame, BrainCircuit } from 'lucide-react';

interface FeedItem {
  id: string;
  type: 'news' | 'market-signal' | 'ai-pick';
  title: string;
  source: string;
  timestamp: string;
  content: string;
  keywords: string[];
}

const mockFeed: FeedItem[] = [
  {
    id: '1',
    type: 'news',
    title: '엔비디아, 차세대 AI 칩 "블랙웰" 공개',
    source: '연합뉴스',
    timestamp: '2시간 전',
    content: '엔비디아가 GPU 기술 컨퍼런스(GTC)에서 차세대 AI 칩 "블랙웰"을 공개했습니다. 기존 호퍼 아키텍처보다 최대 30배의 성능 향상을 제공하며, AI 모델 훈련 및 추론 시간을 대폭 단축시킬 것으로 기대됩니다.',
    keywords: ['엔비디아', 'AI반도체', '신제품']
  },
  {
    id: '2',
    type: 'market-signal',
    title: '미국 소비자물가지수(CPI) 예상 상회, 금리 인하 지연 가능성',
    source: '로이터',
    timestamp: '8시간 전',
    content: '미국의 3월 소비자물가지수(CPI)가 전년 동월 대비 3.5% 상승하여 시장 예상치를 상회했습니다. 이는 연준의 금리 인하 시점이 늦춰질 수 있다는 우려를 낳고 있습니다.',
    keywords: ['거시경제', '금리', 'CPI']
  },
  {
    id: '3',
    type: 'ai-pick',
    title: 'AI가 선정한 오늘의 유망주: MSFT',
    source: 'GenMirae AI',
    timestamp: '1일 전',
    content: '마이크로소프트(MSFT)가 AI 기반 클라우드 서비스 "코파일럿"의 폭발적인 성장에 힘입어 긍정적인 모멘텀을 보이고 있습니다. 최근 기관 투자자들의 매수세가 유입되고 있으며, 장기적인 성장 가능성이 높게 평가됩니다.',
    keywords: ['마이크로소프트', 'AI추천', '클라우드']
  },
];

const FeedItemIcon = ({ type }: { type: FeedItem['type'] }) => {
  switch (type) {
    case 'news':
      return <Newspaper className="w-4 h-4 text-blue-500" />;
    case 'market-signal':
      return <Flame className="w-4 h-4 text-orange-500" />;
    case 'ai-pick':
      return <BrainCircuit className="w-4 h-4 text-purple-500" />;
  }
};

export function InvestmentFeed() {
  return (
    <div className="space-y-4">
      {mockFeed.map((item) => (
        <Card key={item.id} className="p-4">
          <div className="flex items-start space-x-3">
            <div className="mt-1">
              <FeedItemIcon type={item.type} />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-muted-foreground">{item.source} • {item.timestamp}</span>
              </div>
              <h4 className="font-semibold mb-2">{item.title}</h4>
              <p className="text-sm text-muted-foreground mb-3">{item.content}</p>
              <div className="flex flex-wrap gap-2">
                {item.keywords.map((keyword) => (
                  <Button key={keyword} variant="outline" size="sm" className="text-xs h-7 px-2">
                    # {keyword}
                  </Button>
                ))}
              </div>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
} 