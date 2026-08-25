export interface CostDatasetSummary {
  aws_account_id: string | null;
  total_days: number;

  earliest_date: string | null;
  latest_date: string | null;

  total_cost: number;
  minimum_required_days: number;
  ready_for_forecasting: boolean;
}


export interface CostDatasetCollection {
  start_date: string;
  end_date: string;

  api_pages_requested: number;
  days_fetched: number;
  days_saved: number;
}


export interface DailyCostPrediction {
  forecast_date: string;
  predicted_cost: number;
}


export interface CostForecast {
  aws_account_id: string;
  currency: string;
  model_name: string;

  training_start_date: string;
  training_end_date: string;
  training_days: number;

  historical_average_daily_cost: number;
  validation_mae: number;

  forecast_days: number;
  projected_total_cost: number;
  projected_average_daily_cost: number;

  daily_trend: number;
  trend_direction: string;

  predictions: DailyCostPrediction[];

  warning: string;
}


export interface CurrentUser {
  id: number;
  email: string;
  role: string;
}