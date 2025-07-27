import { useState } from "react";
import { Button } from "./components/ui/button";
import { PortfolioChart } from "./components/PortfolioChart";
import { AssetSummaryCards } from "./components/AssetSummaryCards";
import { InvestmentJourney } from "./components/InvestmentJourney";
import { AIChatbot } from "./components/AIChatbot";
import { PerformanceSummary } from "./components/PerformanceSummary";
import { AgentNotifications } from "./components/AgentNotifications";
import { MobileHeader } from "./components/MobileHeader";
import { BottomNavigation } from "./components/BottomNavigation";
import { useMobile } from "./components/ui/use-mobile";
import { MessageCircle } from "lucide-react";

const tabTitles = {
  dashboard: "나만의 맞춤형 애널리스트",
  portfolio: "포트폴리오",
  journey: "투자 여정",
  chat: "AI Analyst",
};

export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const isMobile = useMobile();

  const renderTabContent = () => {
    switch (activeTab) {
      case "dashboard":
        return (
          <div className="space-y-4">
            <AgentNotifications />
            <PerformanceSummary />

            {isMobile ? (
              <div className="space-y-4">
                <PortfolioChart />
                <AssetSummaryCards />
                <div className="flex justify-center py-4">
                  <Button
                    className="flex items-center space-x-2 w-full max-w-xs"
                    onClick={() => setActiveTab("chat")}
                  >
                    <MessageCircle className="w-4 h-4" />
                    <span>AI AI Analyst</span>
                  </Button>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <PortfolioChart />
                <div className="space-y-4">
                  <AssetSummaryCards />
                  <div className="flex justify-center">
                    <Button
                      className="flex items-center space-x-2"
                      onClick={() => setActiveTab("chat")}
                    >
                      <MessageCircle className="w-4 h-4" />
                      <span>AI Analyst</span>
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </div>
        );

      case "portfolio":
        return (
          <div className="space-y-4">
            {isMobile ? (
              <div className="space-y-4">
                <PortfolioChart />
                <AssetSummaryCards />
              </div>
            ) : (
              <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
                <div className="xl:col-span-2">
                  <PortfolioChart />
                </div>
                <div className="space-y-4">
                  <AssetSummaryCards />
                </div>
              </div>
            )}
          </div>
        );

      case "journey":
        return (
          <div className="space-y-4">
            <InvestmentJourney />
            <PerformanceSummary />
          </div>
        );

      case "chat":
        return (
          <div className="space-y-4">
            {isMobile ? (
              <AIChatbot />
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                  <AIChatbot />
                </div>
                <div className="space-y-4">
                  <div className="bg-card rounded-lg p-4 shadow-sm border">
                    <h4 className="mb-3">빠른 분석</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>총 자산:</span>
                        <span>8,000만원</span>
                      </div>
                      <div className="flex justify-between">
                        <span>총 수익률:</span>
                        <span className="text-green-600">
                          +6.07%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>최고 수익 자산:</span>
                        <span>해외 주식 (+6.71%)</span>
                      </div>
                      <div className="flex justify-between">
                        <span>AI 추천:</span>
                        <span className="text-blue-600">
                          분산 투자 유지
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <MobileHeader
        title={tabTitles[activeTab as keyof typeof tabTitles]}
      />

      {/* Main Content */}
      <main
        className={`${isMobile ? "px-4 py-4 pb-20" : "container mx-auto px-4 py-6"}`}
      >
        {renderTabContent()}
      </main>

      {/* Bottom Navigation */}
      {isMobile && (
        <BottomNavigation
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />
      )}

      {/* Desktop Tabs - only show on desktop */}
      {!isMobile && (
        <div className="fixed top-20 left-0 right-0 bg-card/95 backdrop-blur border-b z-30">
          <div className="container mx-auto px-4">
            <div className="flex space-x-8">
              {Object.entries(tabTitles).map(([key, title]) => (
                <button
                  key={key}
                  onClick={() => setActiveTab(key)}
                  className={`py-4 px-2 border-b-2 transition-colors ${
                    activeTab === key
                      ? "border-primary text-primary"
                      : "border-transparent text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {key === "dashboard"
                    ? "애널리스트 에이전트"
                    : title}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}