import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Download, ArrowRight, Loader2, ServerCrash, FileText } from "lucide-react";
import { Button } from "./ui/button";
import { marked } from 'marked'; // marked 라이브러리 임포트

interface StockHolding {
  symbol: string;
  name: string;
}

interface AIReportGeneratorProps {
  stockHoldings: StockHolding[];
}

interface ReportSection {
  heading: string;
  content: string;
}

export function AIReportGenerator({ stockHoldings }: AIReportGeneratorProps) {
  const [selectedStock, setSelectedStock] = useState<StockHolding | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [reportContent, setReportContent] = useState<string | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 리포트 생성 핸들러
  const handleGenerateReport = async (stock: StockHolding) => {
    setSelectedStock(stock);
    setIsLoading(true);
    setReportContent(null);
    setPdfUrl(null);
    setError(null);

    try {
      const response = await fetch('/generate_report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker: stock.symbol,
          report_type: 'full', // 항상 full 리포트를 요청하여 pdf_url을 받음
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '리포트 생성에 실패했습니다.');
      }

      const reportData = await response.json();
      
      // 'marked'를 사용하여 마크다운을 HTML로 변환
      const generatedHTML = `
        <h1 style="font-size: 24px; font-weight: bold; border-bottom: 2px solid #333; padding-bottom: 10px;">
          ${reportData.title}
        </h1>
        <p style="font-size: 12px; color: #666;">리포트 생성일: ${new Date().toLocaleDateString()}</p>
        
        ${reportData.sections.map((section: ReportSection) => `
          <h2 style="font-size: 18px; font-weight: bold; margin-top: 30px; padding-bottom: 5px; border-bottom: 1px solid #eee;">${section.heading}</h2>
          <div class="prose-p:leading-relaxed prose-strong:font-semibold">${marked(section.content)}</div>
        `).join('')}
      `;

      setReportContent(generatedHTML);
      if (reportData.pdf_url) {
        setPdfUrl(reportData.pdf_url);
      }

    } catch (err: any) {
      setError(err.message || "리포트 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.");
    } finally {
      setIsLoading(false);
    }
  };

  // PDF 다운로드 핸들러
  const handleDownloadPdf = () => {
    if (pdfUrl) {
      const downloadUrl = `${window.location.origin}${pdfUrl}`;
      window.open(downloadUrl, '_blank');
    }
  };

  // 초기 화면으로 돌아가기
  const handleGoBack = () => {
    setSelectedStock(null);
    setReportContent(null);
    setPdfUrl(null);
    setIsLoading(false);
    setError(null);
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center text-center p-8 min-h-[400px]">
        <Loader2 className="w-16 h-16 animate-spin text-primary mb-4" />
        <h2 className="text-xl font-bold tracking-tight mb-2">
          {selectedStock?.name} AI 리포트 생성 중...
        </h2>
        <div className="text-muted-foreground">
            <p>최대 1~2분 소요될 수 있습니다.</p>
            <p>잠시만 기다려 주세요.</p>
        </div>
      </div>
    );
  }

  if (reportContent) {
    return (
      <div className="p-4 md:p-6 max-w-4xl mx-auto scrollbar-hide">
        <Card>
          <CardHeader>
            <button onClick={handleGoBack} className="text-sm text-primary hover:underline mb-2 text-left">&larr; 종목 선택으로 돌아가기</button>
            <div className="flex justify-between items-start">
              <CardTitle className="text-2xl">{selectedStock?.name} ({selectedStock?.symbol}) 리포트</CardTitle>
              {pdfUrl && (
                <Button onClick={handleDownloadPdf} variant="outline">
                  <Download className="mr-2 h-4 w-4" />
                  PDF
                 </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="scrollbar-hide">
            <div id="report-content-area" className="prose max-w-none scrollbar-hide" dangerouslySetInnerHTML={{ __html: reportContent }} />
          </CardContent>
        </Card>
      </div>
    );
  }

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

  return (
    <div className="p-4 md:p-6 scrollbar-hide">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center bg-primary/10 p-3 rounded-full mb-4">
            <FileText className="w-8 h-8 text-primary" />
        </div>
        <h1 className="text-3xl font-bold tracking-tight">
          AI 기업 리포트
        </h1>
        <p className="mt-2 max-w-2xl mx-auto text-md text-muted-foreground">
          보유 종목을 선택하여 AI가 생성하는 심층 분석 리포트를 즉시 받아보세요.
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
