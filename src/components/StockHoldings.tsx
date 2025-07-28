import { Card } from './ui/card';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface StockHolding {
  symbol: string;
  name: string;
  quantity: number;
  currentPrice: number;
  change: number;
  changePercent: number;
  value: number;
}

interface StockHoldingsProps {
  stockData: StockHolding[];
  isLoading: boolean;
}

const formatCurrency = (value: number) => {
  return `$${(value / 1000).toLocaleString()}K`;
};

const formatPrice = (price: number) => {
  return `$${price.toFixed(2)}`;
};

export function StockHoldings({ stockData, isLoading }: StockHoldingsProps) {
  if (isLoading) {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">보유 종목 현황</h3>
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <Card key={i} className="p-4 h-[78px] animate-pulse bg-muted/50" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">보유 종목 현황</h3>
      <div className="grid grid-cols-1 gap-3">
        {stockData.map((stock) => (
          <Card key={stock.symbol} className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <h4 className="font-medium text-sm">{stock.symbol}</h4>
                  <span className="text-xs text-muted-foreground">{stock.name}</span>
                </div>
                <div className="flex items-center space-x-2 mt-1">
                  <span className="text-sm font-medium">{formatPrice(stock.currentPrice)}</span>
                  <div className="flex items-center space-x-1">
                    {stock.change > 0 ? (
                      <TrendingUp className="w-3 h-3 text-green-600" />
                    ) : (
                      <TrendingDown className="w-3 h-3 text-red-600" />
                    )}
                    <span 
                      className={`text-xs ${
                        stock.change > 0 ? 'text-green-600' : 'text-red-600'
                      }`}
                    >
                      {stock.change > 0 ? '+' : ''}{stock.change.toFixed(2)} 
                      ({stock.changePercent > 0 ? '+' : ''}{stock.changePercent.toFixed(2)}%)
                    </span>
                  </div>
                </div>
              </div>
              <div className="text-right">
                <p className="text-xs text-muted-foreground">{stock.quantity}주</p>
                <p className="text-sm font-medium">{formatCurrency(stock.value)}</p>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
} 