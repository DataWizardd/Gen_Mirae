import { Card, CardContent } from "./ui/card";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "./ui/table";
import { Badge } from "./ui/badge";
import { Skeleton } from "./ui/skeleton";

export interface WatchlistItem {
  symbol: string;
  name: string;
  price: string;
  change: string;
  changeType: 'increase' | 'decrease';
}

interface WatchlistProps {
  watchlistData: WatchlistItem[];
  isLoading: boolean;
}

export function Watchlist({ watchlistData, isLoading }: WatchlistProps) {
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
            {isLoading ? (
              Array.from({ length: 4 }).map((_, index) => (
                <TableRow key={index}>
                  <TableCell>
                    <Skeleton className="h-5 w-12 mb-1" />
                    <Skeleton className="h-4 w-16" />
                  </TableCell>
                  <TableCell className="text-right">
                    <Skeleton className="h-5 w-20" />
                  </TableCell>
                  <TableCell className="text-right">
                    <Skeleton className="h-6 w-16" />
                  </TableCell>
                </TableRow>
              ))
            ) : (
              watchlistData.map((stock) => (
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
              ))
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
