import { useState } from "react";
// import { Button } from "./components/ui/button";
import { PortfolioChart } from "./components/PortfolioChart";
import { AssetSummaryCards } from "./components/AssetSummaryCards";
import { StockHoldings } from "./components/StockHoldings";
import { InvestmentFeed } from "./components/InvestmentFeed";
import { AIDiscovery } from "./components/AIDiscovery";
import { AIChatbot } from "./components/AIChatbot";
import { PerformanceSummary } from "./components/PerformanceSummary";
import { AgentNotifications } from "./components/AgentNotifications";
import { MobileHeader } from "./components/MobileHeader";
import { BottomNavigation } from "./components/BottomNavigation";
import { Watchlist } from "./components/Watchlist";
// import { MessageCircle } from "lucide-react";

const tabTitles = {
  dashboard: "나만의 맞춤형 애널리스트",
  feed: "투자 피드",
  discovery: "AI 종목 발굴",
  chat: "AI Analyst",
};

export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  // const isMobile = true; // Not used

  const renderTabContent = () => {
    switch (activeTab) {
      case "dashboard":
        return (
          <div className="space-y-4">
            <AgentNotifications />
            <PerformanceSummary />
            <h3 className="text-lg font-semibold">포트폴리오 자산 배분</h3>
            <PortfolioChart />
            <AssetSummaryCards />
            <StockHoldings />
            <h3 className="text-lg font-semibold">관심 종목</h3>
            <Watchlist />
          </div>
        );

      case "feed":
        return <InvestmentFeed />;

      case "discovery":
        return <AIDiscovery />;

      case "chat":
        return <AIChatbot />;

      default:
        return null;
    }
  };
  
  return (
    <div className="iphone-container flex flex-col">
      <MobileHeader
        title={tabTitles[activeTab as keyof typeof tabTitles]}
      />

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