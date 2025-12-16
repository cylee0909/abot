import { fetchJSON } from './http';

export interface Group {
  id: number;
  name: string;
  created_at: string;
}

export interface GroupMember {
  id: number;
  group_id: number;
  stock_code: string;
  created_at: string;
}

/**
 * 获取所有分组
 */
export async function getGroups(): Promise<Group[]> {
  const res = await fetchJSON('/groups');
  return res?.data || [];
}

/**
 * 创建新分组
 */
export async function createGroup(name: string): Promise<Group | null> {
  const res = await fetchJSON('/groups', {
    method: 'POST',
    body: JSON.stringify({ name }),
  });
  return res || null;
}

/**
 * 删除分组
 */
export async function deleteGroup(id: number): Promise<boolean> {
  const res = await fetchJSON(`/groups/${id}`, {
    method: 'DELETE',
  });
  return res?.success || false;
}

/**
 * 获取分组中的所有股票
 */
export async function getGroupStocks(id: number, details: boolean = false): Promise<any[]> {
  const res = await fetchJSON(`/groups/${id}/stocks?details=${details}`);
  return res?.data || [];
}

/**
 * 将股票添加到分组
 */
export async function addStockToGroup(groupId: number, stockCode: string): Promise<boolean> {
  const res = await fetchJSON(`/groups/${groupId}/stocks`, {
    method: 'POST',
    body: JSON.stringify({ stock_code: stockCode }),
  });
  return res?.success || false;
}

/**
 * 从分组中移除股票
 */
export async function removeStockFromGroup(groupId: number, stockCode: string): Promise<boolean> {
  const res = await fetchJSON(`/groups/${groupId}/stocks/${stockCode}`, {
    method: 'DELETE',
  });
  return res?.success || false;
}

/**
 * 获取股票所属的所有分组
 */
export async function getStockGroups(stockCode: string): Promise<Group[]> {
  const res = await fetchJSON(`/stocks/${stockCode}/groups`);
  return res?.data || [];
}
