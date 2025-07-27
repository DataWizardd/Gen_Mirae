import { Card } from './ui/card';
import { Button } from './ui/button';
import { Zap, TrendingUp, BarChart } from 'lucide-react';

interface DiscoveryItem {
  id: string;
  symbol: string;
  name: string;
  description: string;
  reason: string;
  momentumScore: number;
  valuationGrade: string;
}

const mockDiscovery: DiscoveryItem[] = [
  {
    id: '1',
    symbol: 'TSLA',
    name: '테슬라',
    description: '전기차 및 에너지 솔루션 선도 기업',
    reason: '자율주행 기술 FSD v12의 상용화 기대감과 사이버트럭 생산량 증대로 인한 모멘텀 포착',
    momentumScore: 88,
    valuationGrade: 'B+',
  },
  {
    id: '2',
    symbol: 'PLTR',
    name: '팔란티어',
    description: '빅데이터 분석 및 AI 플랫폼 전문 기업',
    reason: '정부 및 국방 부문 계약 확대와 상업용 AI 플랫폼(AIP)의 높은 성장세 감지',
    momentumScore: 92,
    valuationGrade: 'A-',
  },
  {
    id: '3',
    symbol: 'SMCI',
    name: '슈퍼마이크로컴퓨터',
    description: 'AI 서버 및 데이터센터 인프라 제공업체',
    reason: '엔비디아와의 긴밀한 파트너십과 액체 냉각 기술 기반의 고성능 서버 수요 급증',
    momentumScore: 95,
    valuationGrade: 'B',
  },
];

export function AIDiscovery() {
  return (
    <div className="space-y-4">
      {mockDiscovery.map((item) => (
        <Card key={item.id} className="p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-full">
                <Zap className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <h4 className="font-semibold">{item.name} ({item.symbol})</h4>
                <p className="text-xs text-muted-foreground">{item.description}</p>
              </div>
            </div>
            <Button size="sm" variant="outline">
              관심 종목 추가
            </Button>
          </div>
          
          <p className="text-sm text-muted-foreground mb-3">{item.reason}</p>

          <div className="grid grid-cols-2 gap-4 text-center">
            <div className="p-2 rounded-lg bg-muted/50">
              <div className="flex items-center justify-center space-x-1">
                <TrendingUp className="w-4 h-4 text-green-500" />
                <h5 className="text-sm font-medium">모멘텀 점수</h5>
              </div>
              <p className="text-xl font-bold text-green-500">{item.momentumScore}</p>
            </div>
            <div className="p-2 rounded-lg bg-muted/50">
              <div className="flex items-center justify-center space-x-1">
                <BarChart className="w-4 h-4 text-blue-500" />
                <h5 className="text-sm font-medium">가치평가 등급</h5>
              </div>
              <p className="text-xl font-bold text-blue-500">{item.valuationGrade}</p>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
} 