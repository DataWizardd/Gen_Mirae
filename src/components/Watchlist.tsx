import { Card, CardHeader, CardTitle, CardContent } from "./ui/card";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "./ui/table";
import { Badge } from "./ui/badge";

const watchlistData = [
  { symbol: 'AVGO', name: '브로드컴', price: '1,735.04', change: '+2.5%', changeType: 'increase' },
  { symbol: 'META', name: '메타', price: '494.78', change: '-0.8%', changeType: 'decrease' },
  { symbol: 'NFLX', name: '넷플릭스', price: '686.12', change: '+1.2%', changeType: 'increase' },
  { symbol: 'TSLA', name: '테슬라', price: '183.01', change: '-1.5%', changeType: 'decrease' },
];

export function Watchlist() {
  return (
    <Card>
      <CardContent className="pt-4">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>종목</TableHead>
              <TableHead className="text-right">현재가</TableHead>
              <TableHead className="text-right">등락률</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {watchlistData.map((stock) => (
              <TableRow key={stock.symbol}>
                <TableCell>
                  <div className="font-medium">{stock.symbol}</div>
                  <div className="text-xs text-muted-foreground">{stock.name}</div>
                </TableCell>
                <TableCell className="text-right">{stock.price}</TableCell>
                <TableCell className="text-right">
                  <Badge variant={stock.changeType === 'increase' ? 'default' : 'destructive'}>
                    {stock.change}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
} 