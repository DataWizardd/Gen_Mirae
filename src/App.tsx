import { useState, useEffect, useCallback } from "react";
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

const initialWatchlist: Omit<WatchlistItem, 'price' | 'change' | 'changeType'>[] = [
  { symbol: 'AVGO', name: '브로드컴' },
  { symbol: 'META', name: '메타' },
  { symbol: 'NFLX', name: '넷플릭스' },
  { symbol: 'TSLA', name: '테슬라' },
];

type StockDetails = Record<string, { price: number; change: number; changePercent: number; }>;

export default function App() {
  const [stockHoldings, setStockHoldings] = useState<StockHolding[]>([]);
  const [portfolioData, setPortfolioData] = useState<PortfolioData[]>([]);
  const [assetData, setAssetData] = useState<AssetData[]>([]);
  const [watchlistData, setWatchlistData] = useState<WatchlistItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("dashboard");

  const processStockData = useCallback((details: StockDetails) => {
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

    const exchangeRate = 1350;
    const totalValue = updatedStockData.reduce((sum, stock) => sum + stock.value, 0);
    const totalChange = updatedStockData.reduce((sum, stock) => sum + (stock.quantity * stock.change), 0);
    const previousTotalValue = totalValue - totalChange;
    const totalChangePercent = previousTotalValue > 0 ? (totalChange / previousTotalValue) * 100 : 0;
    const totalValueInKRW = totalValue * exchangeRate;

    setPortfolioData([
        { name: '국내 주식', value: 0, color: '#2563eb' },
        { name: '해외 주식', value: totalValueInKRW, color: '#dc2626' },
        { name: '현금', value: 10000000, color: '#16a34a' },
    ]);
    
    setAssetData([
        { name: '국내 주식', value: 0, change: 0, changePercent: 0, color: '#2563eb' },
        { name: '해외 주식', value: totalValue, change: totalChange, changePercent: totalChangePercent, color: '#dc2626'},
        { name: '현금', value: 10000000, change: 0, changePercent: 0, color: '#16a34a' },
    ]);

    const updatedWatchlistData = initialWatchlist.map(stock => {
      const detail = details[stock.symbol] || { price: 0, change: 0, changePercent: 0 };
      const changeType: 'increase' | 'decrease' = detail.changePercent >= 0 ? 'increase' : 'decrease';
      return {
        ...stock,
        price: detail.price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
        change: `${detail.changePercent >= 0 ? '+' : ''}${detail.changePercent.toFixed(1)}%`,
        changeType: changeType,
      };
    });
    setWatchlistData(updatedWatchlistData);
  }, []);

  useEffect(() => {
    const fetchStockDetails = async () => {
      try {
        const allSymbols = Array.from(new Set([...initialPortfolio.map(s => s.symbol), ...initialWatchlist.map(w => w.symbol)]));
        
        const response = await fetch(`/stock-details`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ symbols: allSymbols })
        });

        if (!response.ok) throw new Error('Network response was not ok');
        
        const details: StockDetails = await response.json();
        processStockData(details);

      } catch (error) {
        console.error("Failed to fetch stock details:", error);
        const emptyDetails: StockDetails = {};
        [...initialPortfolio, ...initialWatchlist].forEach(s => {
          emptyDetails[s.symbol] = { price: 0, change: 0, changePercent: 0 };
        });
        processStockData(emptyDetails);
      } finally {
        if (isLoading) setIsLoading(false);
      }
    };

    fetchStockDetails();
    const interval = setInterval(fetchStockDetails, 30000);
    return () => clearInterval(interval);
  }, [processStockData, isLoading]);
  
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
            <Watchlist watchlistData={watchlistData} isLoading={isLoading}/>
          </div>
        );
      case "feed":
        return <InvestmentFeed />;
      case "discovery":
        return <AIDiscovery />;
      case "report":
        const holdingsForReport = stockHoldings.map(({ symbol, name }) => ({ symbol, name }));
        return <AIReportGenerator stockHoldings={holdingsForReport} />;
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
          {activeTab !== 'chat' && <div className="h-16" />}
        </main>
      </div>
      <BottomNavigation activeTab={activeTab} onTabChange={setActiveTab}/>
    </div>
  );
}
