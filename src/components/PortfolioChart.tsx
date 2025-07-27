import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { useTheme } from './ui/use-theme';
import { useMobile } from './ui/use-mobile';

interface PortfolioData {
  name: string;
  value: number;
  color: string;
}

const portfolioData: PortfolioData[] = [
  { name: '국내 주식', value: 0, color: '#2563eb' },
  { name: '해외 주식', value: 35000000, color: '#dc2626' },
  { name: '현금', value: 10000000, color: '#16a34a' },
];

const formatCurrency = (value: number) => {
  return `${(value / 10000).toLocaleString()}만원`;
};

export function PortfolioChart() {
  const { theme } = useTheme();
  const isMobile = useMobile();
  const total = portfolioData.reduce((sum, item) => sum + item.value, 0);

  return (
    <div className="bg-card rounded-lg p-4 shadow-sm border">
      <div className={`${isMobile ? 'h-64' : 'h-80'}`}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={portfolioData}
              cx="50%"
              cy="50%"
              innerRadius={isMobile ? 40 : 60}
              outerRadius={isMobile ? 80 : 120}
              paddingAngle={5}
              dataKey="value"
            >
              {portfolioData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip 
              formatter={(value: number) => formatCurrency(value)}
              contentStyle={{
                backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff',
                border: theme === 'dark' ? '1px solid #374151' : '1px solid #e5e7eb',
                borderRadius: '8px',
                color: theme === 'dark' ? '#f9fafb' : '#111827',
                fontSize: isMobile ? '12px' : '14px'
              }}
            />
            {!isMobile && (
              <Legend 
                formatter={(value, entry) => (
                  <span className="text-foreground text-sm">
                    {value}: {formatCurrency(entry.payload?.value || 0)}
                  </span>
                )}
              />
            )}
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 text-center">
        <p className="text-muted-foreground text-sm">총 자산</p>
        <p className={`${isMobile ? 'text-xl' : 'text-2xl'} font-medium`}>
          {formatCurrency(total)}
        </p>
      </div>
      
      {/* 모바일에서는 범례를 차트 아래에 표시 */}
      {isMobile && (
        <div className="mt-4 space-y-2">
          {portfolioData.map((item) => (
            <div key={item.name} className="flex items-center space-x-3">
              <div className="flex items-center space-x-2">
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-sm">{item.name}</span>
              </div>
              <span className="text-sm font-medium">{formatCurrency(item.value)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}