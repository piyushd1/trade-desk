/**
 * API Client for TradeDesk Backend
 * Handles all API calls with error handling and type safety
 */

import axios, { AxiosError } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response types
export interface ApiResponse<T = any> {
  status: string;
  data?: T;
  message?: string;
  [key: string]: any;
}

export interface BrokerSession {
  user_identifier: string;
  broker: string;
  status: string;
  expires_at: string | null;
  meta: any;
  access_token_preview?: string;
}

export interface RiskConfig {
  id: number;
  user_id: number | null;
  max_position_value: number;
  max_positions: number;
  max_position_pct: number;
  max_order_value: number;
  max_orders_per_day: number;
  ops_limit: number;
  max_daily_loss: number;
  max_weekly_loss: number;
  max_monthly_loss: number;
  max_drawdown_pct: number;
  default_stop_loss_pct: number;
  default_target_profit_pct: number;
  enforce_stop_loss: boolean;
  allow_pre_market: boolean;
  allow_after_market: boolean;
  trading_enabled: boolean;
  additional_limits: any;
  created_at: string;
  updated_at: string;
}

export interface DailyMetrics {
  user_id: number;
  trading_date: string;
  orders_placed: number;
  orders_executed: number;
  orders_rejected: number;
  max_positions_held: number;
  current_positions: number;
  realized_pnl: number;
  unrealized_pnl: number;
  total_pnl: number;
  max_loss_hit: number;
  loss_limit_breached: boolean;
  total_turnover: number;
  risk_breaches: number;
  created_at: string;
  updated_at: string;
}

export interface AuditLog {
  id: number;
  user_id: number | null;
  username: string | null;
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  details: any;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
}

export interface SystemEvent {
  id: number;
  event_type: string;
  severity: string;
  component: string | null;
  message: string;
  details: any;
  stack_trace: string | null;
  created_at: string;
}

export interface RiskBreach {
  id: number;
  user_id: number | null;
  strategy_instance_id: number | null;
  breach_type: string;
  breach_details: any;
  action_taken: string | null;
  created_at: string;
}

export interface ZerodhaSessionResponse {
  status: string;
  session: BrokerSession | null;
}

export interface UpdateZerodhaConfigPayload {
  apiKey: string;
  apiSecret: string;
  redirectUrl?: string;
}

// ===== Portfolio / Zerodha data types =====

export interface Holding {
  tradingsymbol: string;
  exchange: string;
  instrument_token: number;
  isin: string;
  product: string;
  price: number;
  quantity: number;
  used_quantity: number;
  t1_quantity: number;
  realised_quantity: number;
  authorised_quantity: number;
  authorised_date: string;
  opening_quantity: number;
  collateral_quantity: number;
  collateral_type: string;
  discrepancy: boolean;
  average_price: number;
  last_price: number;
  close_price: number;
  pnl: number;
  day_change: number;
  day_change_percentage: number;
}

export interface Position {
  tradingsymbol: string;
  exchange: string;
  instrument_token: number;
  product: string;
  quantity: number;
  overnight_quantity: number;
  multiplier: number;
  average_price: number;
  close_price: number;
  last_price: number;
  value: number;
  pnl: number;
  m2m: number;
  unrealised: number;
  realised: number;
  buy_quantity: number;
  buy_price: number;
  buy_value: number;
  buy_m2m: number;
  sell_quantity: number;
  sell_price: number;
  sell_value: number;
  sell_m2m: number;
  day_buy_quantity: number;
  day_buy_price: number;
  day_buy_value: number;
  day_sell_quantity: number;
  day_sell_price: number;
  day_sell_value: number;
}

export interface PositionsResponse {
  day: Position[];
  net: Position[];
}

export interface MarginSegment {
  enabled: boolean;
  net: number;
  available: {
    adhoc_margin: number;
    cash: number;
    opening_balance: number;
    live_balance: number;
    collateral: number;
    intraday_payin: number;
  };
  utilised: {
    debits: number;
    exposure: number;
    m2m_realised: number;
    m2m_unrealised: number;
    option_premium: number;
    payout: number;
    span: number;
    holding_sales: number;
    turnover: number;
    liquid_collateral: number;
    stock_collateral: number;
    delivery: number;
  };
}

export interface MarginsResponse {
  equity?: MarginSegment;
  commodity?: MarginSegment;
}

// Auth API
export const authApi = {
  getZerodhaLoginUrl: async (state?: string) => {
    const params = state ? `?state=${encodeURIComponent(state)}` : '';
    const { data } = await api.get(`/auth/zerodha/connect${params}`);
    return data;
  },

  getZerodhaSession: async (userIdentifier?: string, includeToken = false) => {
    const params = new URLSearchParams();
    if (userIdentifier) params.append('user_identifier', userIdentifier);
    if (includeToken) params.append('include_token', 'true');

    try {
      const { data } = await api.get<ApiResponse<{ session: BrokerSession | null }>>(
        `/auth/zerodha/session?${params}`
      );
      return data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return { status: 'not_found', session: null };
      }
      throw error;
    }
  },

  updateZerodhaConfig: async ({ apiKey, apiSecret, redirectUrl }: UpdateZerodhaConfigPayload) => {
    const payload: Record<string, string> = {
      api_key: apiKey,
      api_secret: apiSecret,
    };

    if (redirectUrl) {
      payload.redirect_url = redirectUrl;
    }

    const { data } = await api.post('/auth/zerodha/config', payload);
    return data;
  },

  refreshToken: async (userIdentifier?: string) => {
    const params = userIdentifier ? `?user_identifier=${encodeURIComponent(userIdentifier)}` : '';
    const { data} = await api.post(`/auth/zerodha/refresh${params}`);
    return data;
  },

  getRefreshStatus: async () => {
    const { data } = await api.get('/auth/zerodha/refresh/status');
    return data;
  },

  getBrokerStatus: async () => {
    const { data } = await api.get('/auth/brokers/status');
    return data;
  },
};

// Risk API
export const riskApi = {
  getConfig: async (userId?: number) => {
    const params = userId ? `?user_id=${userId}` : '';
    const { data } = await api.get<ApiResponse<{ config: RiskConfig }>>(`/risk/config${params}`);
    return data;
  },

  updateConfig: async (updates: Partial<RiskConfig>, userId?: number) => {
    const params = userId ? `?user_id=${userId}` : '';
    const { data } = await api.put(`/risk/config${params}`, updates);
    return data;
  },

  toggleKillSwitch: async (enabled: boolean, reason?: string, userId?: number) => {
    const params = userId ? `?user_id=${userId}` : '';
    const { data } = await api.post(`/risk/kill-switch${params}`, { enabled, reason });
    return data;
  },

  getKillSwitchStatus: async (userId?: number) => {
    const params = userId ? `?user_id=${userId}` : '';
    const { data } = await api.get(`/risk/kill-switch/status${params}`);
    return data;
  },

  preTradeCheck: async (userId: number, symbol: string, quantity: number, price: number) => {
    const { data } = await api.post('/risk/pre-trade-check', {
      user_id: userId,
      symbol,
      quantity,
      price,
    });
    return data;
  },

  getDailyMetrics: async (userId: number) => {
    const { data } = await api.get<ApiResponse<{ metrics: DailyMetrics }>>(
      `/risk/metrics/daily?user_id=${userId}`
    );
    return data;
  },

  getMetricsHistory: async (userId: number, days = 7) => {
    const { data } = await api.get(`/risk/metrics/history?user_id=${userId}&days=${days}`);
    return data;
  },

  getBreaches: async (userId?: number, breachType?: string, limit = 100, offset = 0) => {
    const params = new URLSearchParams();
    if (userId) params.append('user_id', userId.toString());
    if (breachType) params.append('breach_type', breachType);
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());
    const { data } = await api.get<ApiResponse<{ breaches: RiskBreach[] }>>(
      `/risk/breaches?${params}`
    );
    return data;
  },

  getStatus: async (userId?: number) => {
    const params = userId ? `?user_id=${userId}` : '';
    const { data } = await api.get(`/risk/status${params}`);
    return data;
  },

  checkLimits: async (userId: number) => {
    const { data } = await api.get(`/risk/limits/check?user_id=${userId}`);
    return data;
  },
};

// Audit API
export const auditApi = {
  getLogs: async (action?: string, userId?: number, entityType?: string, limit = 100, offset = 0) => {
    const params = new URLSearchParams();
    if (action) params.append('action', action);
    if (userId) params.append('user_id', userId.toString());
    if (entityType) params.append('entity_type', entityType);
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());
    const { data } = await api.get<ApiResponse<{ logs: AuditLog[] }>>(
      `/audit/logs?${params}`
    );
    return data;
  },

  getLog: async (logId: number) => {
    const { data } = await api.get<ApiResponse<{ log: AuditLog }>>(`/audit/logs/${logId}`);
    return data;
  },

  getSystemEvents: async (eventType?: string, severity?: string, component?: string, limit = 100, offset = 0) => {
    const params = new URLSearchParams();
    if (eventType) params.append('event_type', eventType);
    if (severity) params.append('severity', severity);
    if (component) params.append('component', component);
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());
    const { data } = await api.get<ApiResponse<{ events: SystemEvent[] }>>(
      `/system/events?${params}`
    );
    return data;
  },

  getSystemEvent: async (eventId: number) => {
    const { data } = await api.get<ApiResponse<{ event: SystemEvent }>>(`/system/events/${eventId}`);
    return data;
  },
};

// Health API
export const healthApi = {
  check: async () => {
    const { data } = await api.get('/health/status');
    return data;
  },
};

// Portfolio API — wraps Zerodha portfolio endpoints
export const portfolioApi = {
  /**
   * Get long-term holdings (CNC/delivery positions).
   * @param userIdentifier Zerodha OAuth user identifier stored in localStorage
   */
  getHoldings: async (userIdentifier: string) => {
    const params = new URLSearchParams({ user_identifier: userIdentifier });
    const { data } = await api.get<ApiResponse<Holding[]>>(
      `/data/zerodha/holdings?${params}`
    );
    return data;
  },

  /**
   * Get current day/net positions (intraday + carry-forward).
   * @param userIdentifier Zerodha OAuth user identifier stored in localStorage
   */
  getPositions: async (userIdentifier: string) => {
    const params = new URLSearchParams({ user_identifier: userIdentifier });
    const { data } = await api.get<ApiResponse<PositionsResponse>>(
      `/data/zerodha/positions?${params}`
    );
    return data;
  },

  /**
   * Get account margins / available capital.
   * @param userIdentifier Zerodha OAuth user identifier stored in localStorage
   */
  getMargins: async (userIdentifier: string) => {
    const params = new URLSearchParams({ user_identifier: userIdentifier });
    const { data } = await api.get<ApiResponse<MarginsResponse>>(
      `/data/zerodha/margins?${params}`
    );
    return data;
  },
};

// Error handler
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

