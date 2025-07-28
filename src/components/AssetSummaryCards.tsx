import { Card } from './ui/card';
import { TrendingUp, TrendingDown } from 'lucide-react';
// import { useMobile } from './ui/use-mobile';

export interface AssetData {
  name: string;
  value: number;
  change: number;
  changePercent: number;
  color: string;
}

const formatCurrency = (value: number, assetName: string) => {
  if (assetName === '국내 주식' || assetName === '현금') {
    if (value === 0 && assetName === '국내 주식') return '0원';
    return `${(value / 10000).toLocaleString('ko-KR')}만원`;
  }
  return `$${(value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

export function AssetSummaryCards({ data }: { data: AssetData[] }) {
  // const isMobile = useMobile();

  return (
    <div className="grid grid-cols-3 gap-3">
      {data.map((asset) => (
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
              {formatCurrency(asset.value, asset.name)}
            </p>
            <div className="flex items-start space-x-1">
              {asset.change > 0 ? (
                <TrendingUp className="w-3 h-3 text-green-600 mt-0.5" />
              ) : asset.change < 0 ? (
                <TrendingDown className="w-3 h-3 text-red-600 mt-0.5" />
              ) : (
                <div className="w-3 h-3" />
              )}
              <div
                className={`text-xs leading-tight ${
                  asset.change > 0 
                    ? 'text-green-600' 
                    : asset.change < 0 
                    ? 'text-red-600' 
                    : 'text-muted-foreground'
                }`}
              >
                <div>
                  {asset.change > 0 ? '+' : ''}{formatCurrency(asset.change, asset.name)}
                </div>
                <div>
                  ({asset.changePercent > 0 ? '+' : ''}{asset.changePercent.toFixed(2)}%)
                </div>
              </div>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}