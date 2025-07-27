import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceDot } from 'recharts';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { useState } from 'react';
import { TrendingUp, TrendingDown, Newspaper } from 'lucide-react';
import { useTheme } from './ui/use-theme';

interface JourneyData {
  date: string;
  totalAssets: number;
  events?: {
    type: 'buy' | 'sell' | 'news';
    title: string;
    description: string;
    amount?: number;
  }[];
}

const journeyData: JourneyData[] = [
  { date: '2024-01', totalAssets: 50000000 },
  { date: '2024-02', totalAssets: 52000000 },
  { date: '2024-03', totalAssets: 48000000, events: [{ type: 'sell', title: '삼성전자 매도', description: '시장 변동성으로 인한 부분 매도', amount: -5000000 }] },
  { date: '2024-04', totalAssets: 55000000 },
  { date: '2024-05', totalAssets: 58000000, events: [{ type: 'buy', title: 'KODEX 200 ETF 매수', description: '시장 저점 진입을 위한 매수', amount: 8000000 }] },
  { date: '2024-06', totalAssets: 62000000 },
  { date: '2024-07', totalAssets: 68000000, events: [{ type: 'news', title: '반도체 호황', description: 'AI 붐으로 인한 반도체 섹터 상승' }] },
  { date: '2024-08', totalAssets: 72000000 },
  { date: '2024-09', totalAssets: 78000000 },
  { date: '2024-10', totalAssets: 80000000 },
];

const formatCurrency = (value: number) => {
  return `${(value / 10000).toLocaleString()}만원`;
};

export function InvestmentJourney() {
  const [selectedEvent, setSelectedEvent] = useState<JourneyData | null>(null);
  const { theme } = useTheme();

  const handleDotClick = (data: any) => {
    const eventData = journeyData.find(item => item.date === data.date);
    if (eventData?.events) {
      setSelectedEvent(eventData);
    }
  };

  return (
    <div className="bg-card rounded-lg p-6 shadow-sm border">
      <h3 className="mb-4">투자 여정</h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={journeyData}>
            <CartesianGrid 
              strokeDasharray="3 3" 
              stroke={theme === 'dark' ? '#374151' : '#e2e8f0'} 
            />
            <XAxis 
              dataKey="date" 
              tick={{ fontSize: 12, fill: theme === 'dark' ? '#9ca3af' : '#6b7280' }}
              tickFormatter={(value) => value.substring(5)}
            />
            <YAxis 
              tick={{ fontSize: 12, fill: theme === 'dark' ? '#9ca3af' : '#6b7280' }}
              tickFormatter={(value) => `${(value / 10000000).toFixed(0)}천만`}
            />
            <Tooltip 
              formatter={(value: number) => [formatCurrency(value), '총자산']}
              labelFormatter={(label) => `${label}월`}
              contentStyle={{
                backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff',
                border: theme === 'dark' ? '1px solid #374151' : '1px solid #e5e7eb',
                borderRadius: '8px',
                color: theme === 'dark' ? '#f9fafb' : '#111827'
              }}
            />
            <Line 
              type="monotone" 
              dataKey="totalAssets" 
              stroke="#2563eb" 
              strokeWidth={2}
              dot={{ fill: '#2563eb', strokeWidth: 2, r: 4 }}
            />
            {journeyData.map((item, index) => 
              item.events?.map((event, eventIndex) => (
                <ReferenceDot
                  key={`${index}-${eventIndex}`}
                  x={item.date}
                  y={item.totalAssets}
                  r={8}
                  fill={event.type === 'buy' ? '#16a34a' : event.type === 'sell' ? '#dc2626' : '#f59e0b'}
                  stroke={theme === 'dark' ? '#1f2937' : '#ffffff'}
                  strokeWidth={2}
                  onClick={() => handleDotClick(item)}
                  style={{ cursor: 'pointer' }}
                />
              ))
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
      
      <Dialog open={!!selectedEvent} onOpenChange={() => setSelectedEvent(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              {selectedEvent?.events?.[0]?.type === 'buy' && <TrendingUp className="w-5 h-5 text-green-600" />}
              {selectedEvent?.events?.[0]?.type === 'sell' && <TrendingDown className="w-5 h-5 text-red-600" />}
              {selectedEvent?.events?.[0]?.type === 'news' && <Newspaper className="w-5 h-5 text-yellow-600" />}
              <span>{selectedEvent?.events?.[0]?.title}</span>
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p>{selectedEvent?.events?.[0]?.description}</p>
            {selectedEvent?.events?.[0]?.amount && (
              <p className="text-lg">
                거래금액: {formatCurrency(Math.abs(selectedEvent.events[0].amount))}
              </p>
            )}
            <p className="text-sm text-muted-foreground">
              일시: {selectedEvent?.date}월
            </p>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}