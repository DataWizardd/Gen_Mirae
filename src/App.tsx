import { useState, useEffect } from "react";
// import { Button } from "./components/ui/button";
import { PortfolioChart, PortfolioData } from "./components/PortfolioChart";
import { AssetSummaryCards, AssetData } from "./components/AssetSummaryCards";
import { StockHoldings } from "./components/StockHoldings";
import { InvestmentFeed } from "./components/InvestmentFeed";
import { AIDiscovery } from "./components/AIDiscovery";
import { AIReportGenerator } from "./components/AIReportGenerator";
import { AIChatbot } from "./components/AIChatbot";
import { PerformanceSummary } from "./components/PerformanceSummary";
import { AgentNotifications } from "./components/AgentNotifications";
import { MobileHeader } from "./components/MobileHeader";
import { BottomNavigation } from "./components/BottomNavigation";
import { Watchlist, WatchlistItem } from "./components/Watchlist";
// import { MessageCircle } from "lucide-react";

// StockHolding 인터페이스 정의
export interface StockHolding {
  symbol: string;
  name: string;
  quantity: number;
  avgPrice: number;
  currentPrice: number;
  change: number;
  changePercent: number;
  value: number;
}

const initialPortfolio: Omit<StockHolding, 'currentPrice' | 'change' | 'changePercent' | 'value'>[] = [
  { symbol: 'AAPL', name: '애플', quantity: 10, avgPrice: 150.25 },
  { symbol: 'NVDA', name: '엔비디아', quantity: 5, avgPrice: 220.80 },
  { symbol: 'MSFT', name: '마이크로소프트', quantity: 8, avgPrice: 300.50 },
  { symbol: 'AMZN', name: '아마존', quantity: 15, avgPrice: 180.00 },
  { symbol: 'GOOGL', name: '알파벳', quantity: 12, avgPrice: 140.70 },
];

/*
const tabTitles = {
  dashboard: "나만의 맞춤형 애널리스트",
  feed: "투자 피드",
  discovery: "AI 종목 발굴",
  chat: "AI Analyst",
};
*/

export default function App() {
  const [stockHoldings, setStockHoldings] = useState<StockHolding[]>([]);
  const [portfolioData, setPortfolioData] = useState<PortfolioData[]>([
    { name: '국내 주식', value: 0, color: '#2563eb' },
    { name: '해외 주식', value: 0, color: '#dc2626' },
    { name: '현금', value: 10000000, color: '#16a34a' },
  ]);
  const [assetData, setAssetData] = useState<AssetData[]>([
    { name: '국내 주식', value: 0, change: 0, changePercent: 0, color: '#2563eb' },
    { name: '해외 주식', value: 0, change: 0, changePercent: 0, color: '#dc2626' },
    { name: '현금', value: 10000000, change: 0, changePercent: 0, color: '#16a34a' },
  ]);
  const initialWatchlist = [
    { symbol: 'AVGO', name: '브로드컴' },
    { symbol: 'META', name: '메타' },
    { symbol: 'NFLX', name: '넷플릭스' },
    { symbol: 'TSLA', name: '테슬라' },
  ];
  
  const [watchlistData, setWatchlistData] = useState<WatchlistItem[]>([
    { symbol: 'AVGO', name: '브로드컴', price: '1,735.04', change: '+2.5%', changeType: 'increase' },
    { symbol: 'META', name: '메타', price: '494.78', change: '-0.8%', changeType: 'decrease' },
    { symbol: 'NFLX', name: '넷플릭스', price: '686.12', change: '+1.2%', changeType: 'increase' },
    { symbol: 'TSLA', name: '테슬라', price: '183.01', change: '-1.5%', changeType: 'decrease' },
  ]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("dashboard");
  // const isMobile = true; // Not used

  useEffect(() => {
    const fetchStockDetails = async () => {
      setIsLoading(true);
      try {
        const apiUrl = process.env.REACT_APP_API_URL || '';
        // 포트폴리오 종목과 관심종목을 모두 포함해서 API 호출
        const allSymbols = [
          ...initialPortfolio.map(s => s.symbol),
          ...initialWatchlist.map(w => w.symbol)
        ];
        const response = await fetch(`${apiUrl}/stock-details`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ symbols: allSymbols })
        });
        if (!response.ok) throw new Error('Network response was not ok');
        
        const details: Record<string, { price: number; change: number; changePercent: number; }> = await response.json();
        
        const updatedStockData = initialPortfolio.map(stock => {
          const detail = details[stock.symbol] || { price: 0, change: 0, changePercent: 0 };
          return {
            ...stock,
            currentPrice: detail.price,
            change: detail.change,
            changePercent: detail.changePercent,
            value: stock.quantity * detail.price,
          };
        });
        setStockHoldings(updatedStockData);

        // 포트폴리오 차트 데이터 계산
        const exchangeRate = 1350;
        const overseasValue = updatedStockData.reduce((sum, stock) => sum + stock.value, 0);
        const overseasValueInKRW = overseasValue * exchangeRate;
        
        setPortfolioData(prevData => prevData.map(item => {
          if (item.name === '해외 주식') {
            return { ...item, value: overseasValueInKRW };
          }
          return item;
        }));

        // 자산 요약 카드 데이터 계산
        const totalValue = updatedStockData.reduce((sum, stock) => sum + stock.value, 0);
        const totalChange = updatedStockData.reduce((sum, stock) => sum + (stock.quantity * stock.change), 0);
        const previousTotalValue = totalValue - totalChange;
        const totalChangePercent = previousTotalValue > 0 ? (totalChange / previousTotalValue) * 100 : 0;
        
        setAssetData(prevData => prevData.map(item => {
          if (item.name === '해외 주식') {
            return { 
              ...item, 
              value: totalValue,
              change: totalChange,
              changePercent: totalChangePercent
            };
          }
          return item;
        }));

        // 관심종목 데이터 업데이트
        const updatedWatchlistData = initialWatchlist.map(stock => {
          const detail = details[stock.symbol] || { price: 0, change: 0, changePercent: 0 };
          const changeType: 'increase' | 'decrease' = detail.changePercent >= 0 ? 'increase' : 'decrease';
          return {
            symbol: stock.symbol,
            name: stock.name,
            price: detail.price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
            change: `${detail.changePercent >= 0 ? '+' : ''}${detail.changePercent.toFixed(1)}%`,
            changeType: changeType
          };
        });
        setWatchlistData(updatedWatchlistData);

      } catch (error) {
        console.error("Failed to fetch stock details:", error);
        const errorStockData = initialPortfolio.map(stock => ({
          ...stock,
          currentPrice: 0,
          change: 0,
          changePercent: 0,
          value: 0,
        }));
        setStockHoldings(errorStockData);
      } finally {
        setIsLoading(false);
      }
    };

    fetchStockDetails();
    
    // 실시간 업데이트를 위해 30초마다 데이터 갱신
    const interval = setInterval(fetchStockDetails, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const renderTabContent = () => {
    switch (activeTab) {
      case "dashboard":
        return (
          <div className="space-y-4">
            <AgentNotifications />
            <PerformanceSummary />
            <h3 className="text-lg font-semibold">포트폴리오 자산 배분</h3>
            <PortfolioChart data={portfolioData} />
            <AssetSummaryCards data={assetData} />
            <StockHoldings stockData={stockHoldings} isLoading={isLoading} />
            <h3 className="text-lg font-semibold">관심 종목</h3>
            <Watchlist watchlistData={watchlistData} />
          </div>
        );

      case "feed":
        return <InvestmentFeed />;

      case "discovery":
        return <AIDiscovery />;

      case "report":
        return <AIReportGenerator stockHoldings={stockHoldings} />;

      case "chat":
        return <AIChatbot stockHoldings={stockHoldings} watchlist={watchlistData} />;

      default:
        return null;
    }
  };
  
  return (
    <div className="iphone-container flex flex-col">
      <MobileHeader />

      <div className="flex-1 flex flex-col overflow-y-auto no-scrollbar" style={{paddingBottom: activeTab === 'chat' ? '64px' : '0px'}}>
        <main className="px-4 py-4 space-y-4 flex-1">
          {renderTabContent()}
          {activeTab !== 'chat' && <div className="h-16" />} {/* Add space for scrolling only for non-chat tabs */}
        </main>
      </div>

      <BottomNavigation
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />
    </div>
  );
}