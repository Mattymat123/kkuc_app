import { makeAssistantToolUI } from '@assistant-ui/react'

type GetStockPriceToolArgs = {
    stock_symbol: string;
}

type GetStockPriceToolResult = {
    symbol: string;
    company_name: string;
    current_price: number;
    change: number;
    change_percent: number;
    volume: number;
    market_cap: string;
    pe_ratio: number;
    fifty_two_week_high: number;
    fifty_two_week_low: number;
    timestamp: string;
}

const LoadingSpinner = () => (
    <div className="flex justify-center items-center p-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
    </div>
);

const StockInfoItem = ({ label, value, className = '' }: { label: string; value: string | number; className?: string }) => (
    <div>
        <p className="text-gray-600">{label}</p>
        <p className={`font-semibold ${className}`}>{value}</p>
    </div>
);

const StockPriceDisplay = ({ result }: { result: GetStockPriceToolResult }) => {
    if (!result) return null;
    
    const changeColor = (result.change ?? 0) >= 0 ? 'text-green-600' : 'text-red-600';
    const changePrefix = (result.change ?? 0) >= 0 ? '+' : '';
    
    return (
        <div className="p-4 border rounded-lg shadow-md">
            <h1 className="text-2xl font-bold mb-4">{result.company_name}</h1>
            <div className="grid grid-cols-2 gap-4">
                <StockInfoItem label="Symbol" value={result.symbol ?? 'N/A'} />
                <StockInfoItem label="Current Price" value={`$${result.current_price?.toFixed(2) ?? 'N/A'}`} />
                <StockInfoItem 
                    label="Change" 
                    value={`${changePrefix}${result.change?.toFixed(2) ?? 'N/A'} (${result.change_percent?.toFixed(2) ?? 'N/A'}%)`}
                    className={changeColor}
                />
                <StockInfoItem label="Market Cap" value={result.market_cap ?? 'N/A'} />
                <StockInfoItem label="P/E Ratio" value={result.pe_ratio?.toFixed(2) ?? 'N/A'} />
                <StockInfoItem label="Volume" value={result.volume?.toLocaleString() ?? 'N/A'} />
                <StockInfoItem 
                    label="52 Week Range" 
                    value={`$${result.fifty_two_week_low?.toFixed(2) ?? 'N/A'} - $${result.fifty_two_week_high?.toFixed(2) ?? 'N/A'}`} 
                />
                <StockInfoItem 
                    label="Last Updated" 
                    value={new Date(result.timestamp).toLocaleString()} 
                />
            </div>
        </div>
    );
};

export const GetStockPriceToolUI = makeAssistantToolUI<GetStockPriceToolArgs, GetStockPriceToolResult>({
    toolName: "get_stock_price",
    render: ({ result }) => {
        console.log('result', result);
        if (!result) return <LoadingSpinner />;
        return <StockPriceDisplay result={result} />;
    }
});