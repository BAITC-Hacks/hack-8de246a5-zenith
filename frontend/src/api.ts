export type Stats = {month:string; count:number; income:number; expense:number; balance:number; previous_expense:number; change_percent:number|null; local_count:number; categories:{name:string;amount:number}[]; days:{day:number;income:number;expense:number}[]; top:{id:number;date:string;description:string;amount:number;category:string}[]; forecast:{daily_average:number;projected_expense:number;remaining:number;days_left:number}};
export type InsightData = {observations:{title:string;text:string}[];tips:{title:string;text:string}[];source:string;cached:boolean};
export async function api<T>(path:string, options?:RequestInit):Promise<T> {
  let response:Response;
  try {response = await fetch('/api' + path, options);} catch {throw new Error('Нет связи с сервером. Проверьте, что backend запущен.');}
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(typeof data?.detail === 'string' ? data.detail : 'Не удалось выполнить запрос. Попробуйте ещё раз.');
  }
  return response.json();
}
export const monthLabel = (m:string) => new Date(m + '-01T12:00:00').toLocaleDateString('ru-RU',{month:'long',year:'numeric'}).replace(' г.','');
