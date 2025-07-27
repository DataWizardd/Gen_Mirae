import { Card } from './ui/card';
import { TrendingUp, Target, Calendar, Award } from 'lucide-react';

interface PerformanceMetric {
  title: string;
  value: string;
  icon: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  description: string;
}

const performanceMetrics: PerformanceMetric[] = [
  {
    title: '총 수익률',
    value: '+6.07%',
    icon: <TrendingUp className="w-5 h-5 text-green-600" />,
    trend: 'up',
    description: '전체 포트폴리오 수익률'
  },
  {
    title: '연평균 수익률',
    value: '+12.8%',
    icon: <Target className="w-5 h-5 text-blue-600" />,
    trend: 'up',
    description: '지난 3년 평균'
  },
  {
    title: '투자 기간',
    value: '18개월',
    icon: <Calendar className="w-5 h-5 text-purple-600" />,
    description: '포트폴리오 운용 기간'
  },
  {
    title: '최고 수익률',
    value: '+18.9%',
    icon: <Award className="w-5 h-5 text-yellow-600" />,
    description: '역대 최고 수익률'
  }
];

export function PerformanceSummary() {
  return (
    <div className="space-y-3">
      <h3 className="text-base font-semibold">투자 성과 요약</h3>
      <div className="grid grid-cols-4 gap-2">
        {performanceMetrics.map((metric, index) => (
          <Card key={index} className="p-2">
            <div className="flex flex-col items-center text-center space-y-1">
              <div className="flex items-center space-x-1">
                {metric.icon}
              </div>
              <h4 className="text-xs text-muted-foreground leading-tight">{metric.title}</h4>
              <p className="text-sm font-medium">{metric.value}</p>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}