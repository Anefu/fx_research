//+------------------------------------------------------------------+
//|                                        ExportTicksFromMT5.mq5    |
//|  FX Edge Research - FX-LDN data export script — v1.04            |
//|                                                                  |
//|  Exports tick Bid/Ask for the registry universe into CSVs under  |
//|  Common\Files\FX_EDGE\, one file per pair per month:             |
//|      utc_ms,bid,ask                                              |
//|                                                                  |
//|  v1.04:                                                          |
//|   - default depth = 10 years (120 months), InpMonthsBack input   |
//|   - walks NEWEST -> OLDEST month by month                        |
//|   - stops a pair after N consecutive empty months (data-driven)  |
//|   - per-month file, so interrupted runs resume cleanly           |
//|   - Sleep(50)/month: UI and log stay alive under wine            |
//|                                                                  |
//|  Timestamps: CopyTicksRange time_msc is UTC for this feed        |
//|  (verified: weekly gaps land Fri 23:59 -> Mon 00:00 UTC).        |
//+------------------------------------------------------------------+
#property copyright "FX Edge Research"
#property version   "1.04"
#property script_show_inputs

input string InpSymbols    = "EURUSD,GBPUSD,USDJPY,AUDUSD,USDCAD,USDCHF";
input int    InpMonthsBack = 120;    // months of history to request (10y)
input string InpOutFolder  = "FX_EDGE";
input int    InpMaxEmpty   = 3;      // consecutive empty months before declaring server history exhausted

//+------------------------------------------------------------------+
int DaysInMonth(int m, int y)
{
   static int d[12] = {31,28,31,30,31,30,31,31,30,31,30,31};
   int days = d[m-1];
   if(m == 2 && (y%4==0 && (y%100!=0 || y%400==0))) days = 29;
   return days;
}

//+------------------------------------------------------------------+
long ExportMonth(const string symbol, const int year, const int month)
{
   int dim = DaysInMonth(month, year);
   datetime month_start = StringToTime(StringFormat("%04d.%02d.%02d 00:00", year, month, 1));
   datetime month_end   = StringToTime(StringFormat("%04d.%02d.%02d 23:59:59", year, month, dim));

   // StringToTime is server-local naive; this feed is UTC-aligned (verified),
   // so treat wall time as UTC ms directly.
   ulong from_ms = (ulong)month_start * 1000;
   ulong to_ms   = (ulong)(month_end + 60) * 1000;   // inclusive final minute

   MqlTick ticks[];
   ArrayResize(ticks, 0);
   ResetLastError();
   int got = CopyTicksRange(symbol, ticks, COPY_TICKS_INFO, from_ms, to_ms);
   if(got <= 0)
   {
      int err = GetLastError();
      // 4402 = ERR_HISTORY_NOT_FOUND-equivalent: no data this month
      Print(symbol, " ", StringFormat("%04d%02d", year, month),
            ": no tick data (got=", got, ", err=", err, ")");
      return 0;
   }

   string fname = InpOutFolder + "\\" + symbol + "_ticks_" + StringFormat("%04d%02d", year, month) + ".csv";
   ResetLastError();
   int fh = FileOpen(fname, FILE_READ|FILE_WRITE|FILE_CSV|FILE_COMMON|FILE_ANSI, ',');
   if(fh == INVALID_HANDLE)
   {
      Print(symbol, ": CANNOT OPEN ", fname, " err=", GetLastError());
      return 0;
   }
   FileSeek(fh, 0, SEEK_END);
   if(FileTell(fh) == 0) FileWrite(fh, "utc_ms", "bid", "ask");

   long written = 0;
   for(int i = 0; i < got; i++)
   {
      FileWrite(fh, (long)ticks[i].time_msc,
                DoubleToString(ticks[i].bid, 5),
                DoubleToString(ticks[i].ask, 5));
      written++;
   }
   FileClose(fh);
   Print(symbol, " ", StringFormat("%04d%02d", year, month), ": wrote ", written, " ticks");
   return written;
}

//+------------------------------------------------------------------+
void OnStart()
{
   string symbols[];
   int n = StringSplit(InpSymbols, ',', symbols);
   if(n <= 0) { Print("no symbols parsed from: ", InpSymbols); return; }

   datetime now_utc = TimeGMT();
   MqlDateTime nm;  TimeToStruct(now_utc, nm);

   // walk newest -> oldest, InpMonthsBack months
   int cur_y = nm.year, cur_m = nm.mon;
   int months_done = 0;

   Print("FX_EDGE v1.04 export start: ", InpMonthsBack,
         " months back from ", StringFormat("%04d%02d", cur_y, cur_m),
         " | pairs: ", InpSymbols, " | empty-stop after ", InpMaxEmpty, " consecutive empty months");

   for(int s = 0; s < n; s++)
   {
      string sym = symbols[s];
      StringTrimLeft(sym); StringTrimRight(sym);
      if(sym == "") continue;
      if(!SymbolSelect(sym, true))
      {
         Print(sym, ": NOT IN MARKET WATCH, skipping (open its chart once first)");
         continue;
      }

      long   total = 0;
      int    empty_streak = 0;
      int    y = cur_y, m = cur_m;

      while(months_done < InpMonthsBack)
      {
         long got = ExportMonth(sym, y, m);
         total += got;

         if(got == 0)
         {
            empty_streak++;
            if(empty_streak >= InpMaxEmpty)
            {
               Print(sym, ": ", InpMaxEmpty, " consecutive empty months -> server history exhausted at ",
                     StringFormat("%04d%02d", y, m), " (pair stopped after writing ", total, " ticks)");
               break;
            }
         }
         else empty_streak = 0;

         m--; if(m == 0) { m = 12; y--; }
         months_done++;
         Sleep(50);   // yield: keeps UI/log alive under wine
      }
      Print(sym, ": DONE, total ticks written = ", total);
      months_done = 0;   // reset per pair
      Sleep(100);
   }
   Print("FX_EDGE export complete.");
}
//+------------------------------------------------------------------+