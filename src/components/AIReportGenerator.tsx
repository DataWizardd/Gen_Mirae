import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Download, ArrowRight, Loader2, ServerCrash } from "lucide-react";
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import { Button } from "./ui/button";

// App.tsx로부터 받을 보유 종목 데이터 타입
interface StockHolding {
  symbol: string;
  name: string;
}

interface AIReportGeneratorProps {
  stockHoldings: StockHolding[];
}

export function AIReportGenerator({ stockHoldings }: AIReportGeneratorProps) {
  const [selectedStock, setSelectedStock] = useState<StockHolding | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [reportContent, setReportContent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 리포트 생성 핸들러
  const handleGenerateReport = async (stock: StockHolding) => {
    setSelectedStock(stock);
    setIsLoading(true);
    setReportContent(null);
    setError(null);

    // 실제 LLM API 호출을 시뮬레이션하기 위한 딜레이
    await new Promise(resolve => setTimeout(resolve, 2000));

    try {
      // 이 부분에서 실제 LLM API를 호출하여 리포트 내용을 받아옵니다.
      // 현재는 샘플 HTML로 대체합니다.
      const generatedHTML = `
        <h1 style="font-size: 24px; font-weight: bold; border-bottom: 2px solid #333; padding-bottom: 10px;">
          AI 기반 기업 리포트: ${stock.name} (${stock.symbol})
        </h1>
        <p style="font-size: 12px; color: #666;">리포트 생성일: ${new Date().toLocaleDateString()}</p>
        
        <h2 style="font-size: 18px; font-weight: bold; margin-top: 30px;">1. 기업 개요</h2>
        <p><strong>${stock.name}</strong>는 혁신적인 기술과 강력한 브랜드 파워를 바탕으로 각 산업 분야에서 선도적인 위치를 차지하고 있습니다. (이하 LLM 생성 내용)</p>
        
        <h2 style="font-size: 18px; font-weight: bold; margin-top: 30px;">2. 투자 하이라이트</h2>
        <ul>
          <li><strong>강력한 시장 지배력:</strong> 핵심 사업 분야에서 높은 점유율을 유지하고 있습니다.</li>
          <li><strong>지속적인 연구개발 투자:</strong> 미래 성장 동력 확보를 위한 R&D 투자를 아끼지 않고 있습니다.</li>
          <li><strong>안정적인 재무 구조:</strong> 꾸준한 현금 흐름과 낮은 부채 비율을 자랑합니다.</li>
        </ul>
        
        <h2 style="font-size: 18px; font-weight: bold; margin-top: 30px;">3. 리스크 분석</h2>
        <p>글로벌 경기 둔화에 따른 수요 감소 가능성과 주요 시장에서의 경쟁 심화는 잠재적인 리스크 요인입니다.</p>
        
        <h2 style="font-size: 18px; font-weight: bold; margin-top: 30px;">4. 종합 의견</h2>
        <p>단기적인 변동성은 존재할 수 있으나, 장기적인 관점에서 동사의 성장 잠재력은 여전히 유효하다고 판단됩니다.</p>
      `;
      setReportContent(generatedHTML);
    } catch (err) {
      setError("리포트 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.");
    } finally {
      setIsLoading(false);
    }
  };

  // PDF 다운로드 핸들러
  const handleDownloadPdf = async () => {
    const reportElement = document.getElementById('report-content-area');
    if (!reportElement) return;

    const canvas = await html2canvas(reportElement, { scale: 2 });
    const imgData = canvas.toDataURL('image/png');
    const pdf = new jsPDF({ orientation: 'p', unit: 'mm', format: 'a4' });
    const imgProps= pdf.getImageProperties(imgData);
    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;
    
    pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
    pdf.save(`AI_Report_${selectedStock?.symbol}_${new Date().toISOString().split('T')[0]}.pdf`);
  };

  // 초기 화면으로 돌아가기
  const handleGoBack = () => {
    setSelectedStock(null);
    setReportContent(null);
    setIsLoading(false);
    setError(null);
  };

  // 화면 렌더링 로직
  // 1. 리포트 생성 중 (로딩)
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center text-center p-8 min-h-[400px]">
        <Loader2 className="w-16 h-16 animate-spin text-primary mb-4" />
        <h2 className="text-2xl font-bold tracking-tight">
          {selectedStock?.name} AI 리포트 생성 중...
        </h2>
        <p className="text-muted-foreground">잠시만 기다려 주세요.</p>
      </div>
    );
  }

  // 2. 리포트 생성 완료
  if (reportContent) {
    return (
      <div className="p-4 md:p-6 max-w-4xl mx-auto scrollbar-hide">
         <Card>
          <CardHeader>
             <button onClick={handleGoBack} className="text-sm text-primary hover:underline mb-2 text-left">&larr; 종목 선택으로 돌아가기</button>
            <CardTitle className="text-2xl">{selectedStock?.name} ({selectedStock?.symbol}) 리포트</CardTitle>
          </CardHeader>
          <CardContent className="scrollbar-hide">
            <div id="report-content-area" className="prose max-w-none scrollbar-hide" dangerouslySetInnerHTML={{ __html: reportContent }} />
          </CardContent>
         </Card>
        <div className="sticky bottom-0 bg-background/90 backdrop-blur-sm p-4 mt-4 border-t border-border rounded-t-lg">
            <Button onClick={handleDownloadPdf} className="w-full">
              <Download className="mr-2 h-4 w-4" />
              PDF로 다운로드
            </Button>
        </div>
      </div>
    );
  }

  // 3. 리포트 생성 중 오류 발생
  if (error) {
      return (
        <div className="flex flex-col items-center justify-center text-center p-8 min-h-[400px]">
            <ServerCrash className="w-16 h-16 text-destructive mb-4" />
            <h2 className="text-2xl font-bold tracking-tight text-destructive">오류 발생</h2>
            <p className="text-muted-foreground mb-4">{error}</p>
            <Button onClick={handleGoBack}>다시 시도하기</Button>
        </div>
      )
  }

  // 4. 초기 종목 선택 화면
  return (
    <div className="p-4 md:p-6 scrollbar-hide">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
          AI 기업 리포트
        </h1>
        <p className="mt-2 max-w-2xl mx-auto text-md text-gray-500">
          AI를 통해 심층 분석 리포트를 즉시 받아보세요.
        </p>
      </div>

      <Card className="w-full max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle className="font-bold">보유 종목 목록</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col space-y-2">
            {stockHoldings.length > 0 ? (
              stockHoldings.map((stock) => (
                <button
                  key={stock.symbol}
                  className="w-full text-left p-4 rounded-lg hover:bg-muted transition-colors flex justify-between items-center border"
                  onClick={() => handleGenerateReport(stock)}
                >
                  <div>
                    <p className="font-semibold text-lg">{stock.name}</p>
                    <p className="text-sm text-muted-foreground">{stock.symbol}</p>
                </div>
                  <ArrowRight className="w-5 h-5 text-muted-foreground" />
                </button>
              ))
            ) : (
              <p className="text-muted-foreground text-center py-8">
                리포트를 발행할 보유 종목이 없습니다.
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 