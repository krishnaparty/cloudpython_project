export interface ResourceOverview {
  total: number;
  running: number;
  stopped: number;
  other_states: number;
  compliant: number;
  non_compliant: number;
}

export interface SeverityOverview {
  total: number;
  high: number;
  medium: number;
  low: number;
}

export interface CostHistoryPoint {
  cost_date: string;
  total_cost: number;
  currency: string;
  estimated: boolean;
}

export interface DashboardOverview {
  user_role: string;

  resources: ResourceOverview;
  recommendations: SeverityOverview;
  anomalies: SeverityOverview;

  cost_visible: boolean;
  month_to_date_cost: number | null;
  latest_cost_date: string | null;
  recent_cost_history: CostHistoryPoint[];

  resources_last_synced_at: string | null;
  generated_at: string;
}