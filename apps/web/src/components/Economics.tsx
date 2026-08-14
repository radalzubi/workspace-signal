"use client";
import { useState } from "react";
import { money } from "@/lib/api";

export function Economics() {
  const [result, setResult] = useState<Record<string, number> | null>(null);
  async function calculate(form: FormData) {
    const number = (key: string) => Number(form.get(key));
    const payload = { impressions:number("impressions"), ctr:number("ctr")/100, conversion_rate:number("conversion")/100, average_order_value:number("aov"), commission_rate:number("commission")/100, ad_cpc:number("cpc"), ad_cpm:0, ai_cost:number("ai"), infrastructure_cost:number("infra") };
    const response = await fetch("/api/proxy/unit-economics", {method:"POST", headers:{"content-type":"application/json"}, body:JSON.stringify(payload)});
    setResult(await response.json());
  }
  return <section className="panel economics"><div className="panel-head"><div><p className="eyebrow">SCENARIO MODEL</p><h2>Unit economics calculator</h2></div></div>
    <form action={calculate} className="economics-form">{[["impressions","Impressions","100000"],["ctr","CTR %","1.8"],["conversion","Conversion %","3.5"],["aov","Average order value","65"],["commission","Commission %","6"],["cpc","Ad CPC","0"],["ai","AI cost","15"],["infra","Infrastructure","45"]].map(([name,label,value])=><label key={name}>{label}<input name={name} type="number" step="0.01" defaultValue={value}/></label>)}<button className="primary" type="submit">Calculate economics</button></form>
    {result && <div className="economics-result"><div><span>Revenue</span><b>{money(result.revenue)}</b></div><div><span>Gross profit</span><b className={result.gross_profit >= 0 ? "positive":"negative"}>{money(result.gross_profit)}</b></div><div><span>Break-even CPC</span><b>{money(result.break_even_cpc)}</b></div><div><span>Break-even CPM</span><b>{money(result.break_even_cpm)}</b></div></div>}
  </section>;
}
