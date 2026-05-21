export default function FinancialSummary({ balance, totalPaid }: { balance: number; totalPaid: number }) {
  return (
    <div className="bg-card border border-border p-6 rounded-2xl shadow-sm">
      <h3 className="text-lg font-bold mb-4">Financial Summary</h3>
      <div className="space-y-4">
        <div>
          <p className="text-sm text-muted-foreground">Total Paid</p>
          <p className="text-2xl font-bold text-emerald-600">{totalPaid.toLocaleString()} UZS</p>
        </div>
        <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
          <div className="h-full bg-emerald-500 w-3/4"></div>
        </div>
        <div className="p-4 bg-rose-50 border border-rose-100 rounded-xl">
          <p className="text-sm text-rose-600 font-medium">Current Balance (Due)</p>
          <p className="text-2xl font-bold text-rose-700">{balance.toLocaleString()} UZS</p>
        </div>
      </div>
    </div>
  );
}