import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type {
  DailyCostPrediction,
} from "../types/costForecast";

interface ForecastChartProps {
  predictions: DailyCostPrediction[];
  currency: string;
}

export function ForecastChart({
  predictions,
  currency,
}: ForecastChartProps) {
  const chartData = predictions.map(
    (prediction) => ({
      date: new Date(
        `${prediction.forecast_date}T00:00:00`,
      ).toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
      }),

      cost: prediction.predicted_cost,
    }),
  );

  if (chartData.length === 0) {
    return (
      <div className="empty-state">
        Forecast data available nahi hai.
      </div>
    );
  }

  return (
    <div className="chart-container">
      <ResponsiveContainer
        width="100%"
        height="100%"
      >
        <LineChart
          data={chartData}
          margin={{
            top: 10,
            right: 12,
            left: 0,
            bottom: 0,
          }}
        >
          <CartesianGrid
            strokeDasharray="4 4"
            vertical={false}
            stroke="#e8edf4"
          />

          <XAxis
            dataKey="date"
            axisLine={false}
            tickLine={false}
            tick={{
              fill: "#667085",
              fontSize: 12,
            }}
          />

          <YAxis
            axisLine={false}
            tickLine={false}
            width={65}
            tick={{
              fill: "#667085",
              fontSize: 12,
            }}
            tickFormatter={(value: number) =>
              `$${value.toFixed(2)}`
            }
          />

          <Tooltip
            formatter={(value) => [
              `${currency} ${Number(
                value,
              ).toFixed(6)}`,
              "Predicted cost",
            ]}
            contentStyle={{
              border:
                "1px solid #dfe7f1",
              borderRadius: "10px",
            }}
          />

          <Line
            type="monotone"
            dataKey="cost"
            stroke="#6941c6"
            strokeWidth={3}
            dot={{
              fill: "#6941c6",
              r: 3,
            }}
            activeDot={{
              r: 6,
            }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}