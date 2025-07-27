import { Card } from './ui/card';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface StockData {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  shares: number;
  value: number;
}

const stockData: StockData[] = [
  {
    symbol: 'AAPL',
    name: '애플',
    price: 230.50,
    change: 2.30,
    changePercent: 1.01,
    shares: 10,
    value: 2305000
  },
  {
    symbol: 'NVDA',
    name: '엔비디아',
    price: 875.20,
    change: -8.50,
    changePercent: -0.96,
    shares: 5,
    value: 4376000
  },
  {
    symbol: 'MSFT',
    name: '마이크로소프트',
    price: 425.80,
    change: 5.20,
    changePercent: 1.24,
    shares: 8,
    value: 3406400
  },
  {
    symbol: 'AMZN',
    name: '아마존',
    price: 185.60,
    change: -1.20,
    changePercent: -0.64,
    shares: 15,
    value: 2784000
  },
  {
    symbol: 'GOOGL',
    name: '알파벳',
    price: 172.30,
    change: 3.10,
    changePercent: 1.83,
    shares: 12,
    value: 2067600
  }
];

const formatCurrency = (value: number) => {
  return `${(value / 1000).toLocaleString()}K원`;
};

const formatPrice = (price: number) => {
  return `$${price.toFixed(2)}`;
};

export function StockHoldings() {
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
                  <span className="text-sm font-medium">{formatPrice(stock.price)}</span>
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
                <p className="text-xs text-muted-foreground">{stock.shares}주</p>
                <p className="text-sm font-medium">{formatCurrency(stock.value)}</p>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
} 