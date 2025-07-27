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
    <div className="space-y-4">
      <h3>투자 성과 요약</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {performanceMetrics.map((metric, index) => (
          <Card key={index} className="p-4">
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center space-x-2">
                {metric.icon}
                <h4 className="text-sm text-muted-foreground">{metric.title}</h4>
              </div>
            </div>
            <div className="space-y-1">
              <p className="text-xl font-medium">{metric.value}</p>
              <p className="text-xs text-muted-foreground">{metric.description}</p>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}