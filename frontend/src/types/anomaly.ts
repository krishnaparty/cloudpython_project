export interface MetricCollectionResponse {
  resources_scanned: number;
  datapoints_fetched: number;
  datapoints_saved: number;
}

export interface DatasetSummary {
  resource_count: number;
  total_datapoints: number;

  earliest_timestamp: string | null;
  latest_timestamp: string | null;

  minimum_points_per_resource: number;
  recommended_minimum_points: number;
  ready_for_ml: boolean;
}

export interface AnomalyDetectionResponse {
  resources_found: number;
  resources_trained: number;
  resources_skipped: number;
  points_analyzed: number;
  anomalies_detected: number;
  model_name: string;
}

export interface MetricAnomaly {
  id: number;

  resource_id: string;
  resource_name: string | null;

  metric_name: string;
  metric_timestamp: string;

  average_value: number;
  maximum_value: number;

  anomaly_score: number;
  severity: string;
  reason: string;

  model_name: string;
  is_active: boolean;
  detected_at: string;
}

export interface CurrentUser {
  id: number;
  email: string;
  role: string;
}