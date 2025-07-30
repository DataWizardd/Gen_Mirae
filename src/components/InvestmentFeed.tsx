import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { ThumbsUp, ThumbsDown, BotMessageSquare, Newspaper, FileText, Users, FlaskConical } from 'lucide-react';

interface InsightData {
  id: number;
  symbol: string;
  companyName: string;
  aiSummary: string;
  newsSummary: string;
  disclosureSummary: string;
  reportSummary: string;
  communitySummary: string;
}

const mockInsightData: InsightData[] = [
  {
    id: 1,
    symbol: 'NVDA',
    companyName: '엔비디아',
    aiSummary: '엔비디아는 AI 칩 시장의 지배력을 바탕으로 긍정적인 전망이 우세합니다. 최근 실적 발표는 시장 기대치를 상회했으며, 다수의 증권사에서 목표 주가를 상향 조정했습니다. 다만, 미-중 갈등으로 인한 규제 리스크와 경쟁 심화 가능성은 잠재적인 위험 요인입니다.',
    newsSummary: '블룸버그 통신은 엔비디아의 차세대 GPU "블랙웰"이 AI 시장의 판도를 바꿀 것이라고 보도했습니다. 로이터는 중국으로의 반도체 수출 규제가 엔비디아의 매출에 미칠 영향에 주목하고 있습니다.',
    disclosureSummary: '최근 제출된 10-K 보고서에 따르면, 데이터 센터 부문의 매출이 전년 동기 대비 217% 증가했습니다. CEO 젠슨 황은 스톡옵션을 일부 행사하여 주식을 매각했다고 공시했습니다.',
    reportSummary: '골드만삭스는 엔비디아의 목표주가를 $1,85로 상향 조정하며, AI 산업의 최대 수혜주로 평가했습니다. 모건스탠리는 투자의견 "비중 확대"를 유지하며, 소프트웨어 및 서비스 부문의 성장을 긍정적으로 전망했습니다.',
    communitySummary: '레딧의 r/wallstreetbets 커뮤니티에서는 엔비디아의 단기 주가 변동성에 대한 갑론을박이 활발합니다. 일부는 추가 상승을 기대하며 롱 포지션을, 다른 일부는 고평가를 이유로 숏 포지션을 취하고 있습니다.',
  },
  {
    id: 2,
    symbol: 'AAPL',
    companyName: '애플',
    aiSummary: '애플은 Vision Pro 출시와 AI 기능 강화에 대한 기대로 주가가 반등하고 있습니다. 서비스 부문의 꾸준한 성장이 아이폰 판매 둔화 우려를 일부 상쇄하고 있습니다. M4 칩을 탑재한 새로운 iPad Pro의 초기 시장 반응이 긍정적입니다.',
    newsSummary: 'CNBC는 애플이 오픈AI와 협력하여 iOS 18에 생성형 AI 기능을 탑재할 가능성이 높다고 보도했습니다. 월스트리트저널은 중국 시장에서의 아이폰 판매량 감소가 2분기 연속 이어지고 있다고 전했습니다.',
    disclosureSummary: '애플은 자사주 매입 및 배당금 증액 계획을 발표했습니다. 팀 쿡 CEO는 최근 인터뷰에서 AI 분야에 대한 막대한 투자를 지속할 것이라고 밝혔습니다.',
    reportSummary: 'JP모건은 애플의 서비스 부문 가치를 재평가하며 투자의견을 "매수"로 유지했습니다. 뱅크오브아메리카는 Vision Pro의 초기 판매량이 예상을 하회할 수 있다며 신중한 입장을 보였습니다.',
    communitySummary: '트위터에서는 애플의 AI 전략이 경쟁사에 비해 뒤처지고 있다는 비판과, 애플 특유의 생태계 통합으로 결국 승리할 것이라는 의견이 대립하고 있습니다.',
  },
];

const sourceIcons = {
  news: <Newspaper className="w-4 h-4" />,
  disclosure: <FileText className="w-4 h-4" />,
  report: <FlaskConical className="w-4 h-4" />,
  community: <Users className="w-4 h-4" />,
};

export function InvestmentFeed() {
  const [feedback, setFeedback] = useState<{ [key: number]: 'like' | 'dislike' | null }>({});

  const handleFeedback = (id: number, type: 'like' | 'dislike') => {
    setFeedback(prev => ({ ...prev, [id]: prev[id] === type ? null : type }));
  };

  return (
    <div className="p-4 md:p-6 space-y-6 bg-background min-h-screen">
      <div className="flex flex-col space-y-1 text-center">
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight">AI 인사이트</h1>
        <p className="text-muted-foreground text-xs md:text-sm">AI가 요약한 종목별 핵심 정보를 확인하세요.</p>
      </div>
      <div className="space-y-4">
        {mockInsightData.map((item) => (
          <Card key={item.id} className="overflow-hidden shadow-sm hover:shadow-md transition-shadow duration-300 bg-card">
            <CardHeader className="p-4 border-b">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <h2 className="text-xl font-bold">{item.companyName}</h2>
                  <Badge variant="secondary">{item.symbol}</Badge>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant={feedback[item.id] === 'like' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => handleFeedback(item.id, 'like')}
                    className={`h-8 w-8 p-0 ${feedback[item.id] === 'like' ? 'text-white' : 'text-muted-foreground'}`}
                  >
                    <ThumbsUp className="h-4 w-4" />
                  </Button>
                  <Button
                    variant={feedback[item.id] === 'dislike' ? 'destructive' : 'ghost'}
                    size="sm"
                    onClick={() => handleFeedback(item.id, 'dislike')}
                    className={`h-8 w-8 p-0 ${feedback[item.id] === 'dislike' ? 'text-white' : 'text-muted-foreground'}`}
                  >
                    <ThumbsDown className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-4">
              <div className="flex items-start gap-3 mb-4 pb-4 border-b">
                <BotMessageSquare className="w-7 h-7 text-primary flex-shrink-0 mt-1" />
                <div>
                  <h3 className="font-semibold text-md text-primary">AI 종합 의견</h3>
                  <p className="text-foreground text-sm leading-relaxed">{item.aiSummary}</p>
                </div>
              </div>

              <Tabs defaultValue="news" className="w-full">
                <TabsList className="grid w-full grid-cols-4 h-auto">
                  <TabsTrigger value="news" className="flex flex-col h-full items-center justify-center gap-1 p-2 text-[11px] leading-none">
                    {sourceIcons.news}
                    <span>뉴스</span>
                  </TabsTrigger>
                  <TabsTrigger value="disclosure" className="flex flex-col h-full items-center justify-center gap-1 p-2 text-[11px] leading-none">
                    {sourceIcons.disclosure}
                    <span>공시</span>
                  </TabsTrigger>
                  <TabsTrigger value="report" className="flex flex-col h-full items-center justify-center gap-1 p-2 text-[11px] leading-none">
                    {sourceIcons.report}
                    <span>리포트</span>
                  </TabsTrigger>
                  <TabsTrigger value="community" className="flex flex-col h-full items-center justify-center gap-1 p-2 text-[11px] leading-none">
                    {sourceIcons.community}
                    <span>커뮤니티</span>
                  </TabsTrigger>
                </TabsList>
                <div className="mt-4 p-4 bg-muted rounded-md min-h-[120px]">
                  <TabsContent value="news">
                    <p className="text-sm text-muted-foreground leading-relaxed">{item.newsSummary}</p>
                  </TabsContent>
                  <TabsContent value="disclosure">
                    <p className="text-sm text-muted-foreground leading-relaxed">{item.disclosureSummary}</p>
                  </TabsContent>
                  <TabsContent value="report">
                    <p className="text-sm text-muted-foreground leading-relaxed">{item.reportSummary}</p>
                  </TabsContent>
                  <TabsContent value="community">
                    <p className="text-sm text-muted-foreground leading-relaxed">{item.communitySummary}</p>
                  </TabsContent>
                </div>
              </Tabs>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
} 