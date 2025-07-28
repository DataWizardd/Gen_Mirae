import { Card, CardContent } from "./ui/card";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "./ui/table";
import { Badge } from "./ui/badge";

export interface WatchlistItem {
  symbol: string;
  name: string;
  price: string;
  change: string;
  changeType: 'increase' | 'decrease';
}

export function Watchlist({ watchlistData }: { watchlistData: WatchlistItem[] }) {
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