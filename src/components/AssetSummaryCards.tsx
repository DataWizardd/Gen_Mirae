import { Card } from './ui/card';
import { TrendingUp, TrendingDown } from 'lucide-react';
// import { useMobile } from './ui/use-mobile';

interface AssetData {
  name: string;
  value: number;
  change: number;
  changePercent: number;
  color: string;
}

const assetData: AssetData[] = [
  {
    name: '국내 주식',
    value: 0,
    change: 0,
    changePercent: 0,
    color: '#2563eb'
  },
  {
    name: '해외 주식',
    value: 35000000,
    change: 2200000,
    changePercent: 6.71,
    color: '#dc2626'
  },
  {
    name: '현금',
    value: 10000000,
    change: 0,
    changePercent: 0,
    color: '#16a34a'
  }
];

const formatCurrency = (value: number) => {
  return `${(value / 10000).toLocaleString()}만원`;
};

export function AssetSummaryCards() {
  // const isMobile = useMobile();

  return (
    <div className="grid grid-cols-3 gap-3">
      {assetData.map((asset) => (
        <Card key={asset.name} className="p-3">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-xs font-medium">{asset.name}</h4>
            <div 
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: asset.color }}
            />
          </div>
          <div className="space-y-2">
            <p className="text-sm font-medium">
              {formatCurrency(asset.value)}
            </p>
            <div className="flex items-center space-x-1">
              {asset.change > 0 ? (
                <TrendingUp className="w-3 h-3 text-green-600" />
              ) : asset.change < 0 ? (
                <TrendingDown className="w-3 h-3 text-red-600" />
              ) : (
                <div className="w-3 h-3" />
              )}
              <span 
                className={`text-xs ${
                  asset.change > 0 
                    ? 'text-green-600' 
                    : asset.change < 0 
                    ? 'text-red-600' 
                    : 'text-muted-foreground'
                }`}
              >
                {asset.change > 0 ? '+' : ''}{formatCurrency(asset.change)} 
                ({asset.changePercent > 0 ? '+' : ''}{asset.changePercent}%)
              </span>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}