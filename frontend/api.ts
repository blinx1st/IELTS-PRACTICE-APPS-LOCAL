export class ApiError extends Error { status: number; constructor(message:string,status:number){super(message);this.status=status;} }
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response;
  try { response = await fetch('/api' + path, { ...options, headers: { ...(options.body instanceof FormData ? {} : {'Content-Type':'application/json'}), ...options.headers } }); }
  catch { throw new ApiError('Chưa kết nối được dịch vụ local. Bản nháp vẫn được giữ trên trình duyệt.',0); }
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new ApiError(typeof data.detail === 'string' ? data.detail : 'Dữ liệu không hợp lệ. Vui lòng thử lại.', response.status);
  }
  return response.json();
}
export const post = <T>(path:string,body?:unknown) => api<T>(path,{method:'POST',body: body === undefined ? undefined : JSON.stringify(body)});
