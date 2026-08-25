export interface OptimizationRecommendation {
  id: number;
  resource_db_id: number;

  resource_id: string;
  resource_name: string | null;

  recommendation_type: string;
  severity: string;
  reason: string;

  average_cpu: number | null;
  maximum_cpu: number | null;
  lookback_days: number;

  status: string;
  created_at: string;
  updated_at: string;
}

export interface OptimizationScanResponse {
  scanned_resources: number;
  recommendations_created: number;
  recommendations_updated: number;
  healthy_resources: number;
}

export interface CurrentUser {
  id: number;
  email: string;
  role: string;
}