import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type {
  CostHistoryPoint,
} from "../types/dashboard";

interface CostChartProps {
  data: CostHistoryPoint[];
}

export function CostChart({
  data,
}: CostChartProps) {
  const chartData = data.map((item) => ({
    date: new Date(
      `${item.cost_date}T00:00:00`,
    ).toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
    }),

    cost: item.total_cost,
  }));

  if (chartData.length === 0) {
    return (
      <div className="empty-state">
        Cost dataset collect nahi hua hai.
      </div>
    );
  }

  return (
    <div className="chart-container">
      <ResponsiveContainer
        width="100%"
        height="100%"
      >
        <AreaChart
          data={chartData}
          margin={{
            top: 10,
            right: 12,
            left: 0,
            bottom: 0,
          }}
        >
          <defs>
            <linearGradient
              id="costGradient"
              x1="0"
              y1="0"
              x2="0"
              y2="1"
            >
              <stop
                offset="5%"
                stopColor="#246bfd"
                stopOpacity={0.3}
              />

              <stop
                offset="95%"
                stopColor="#246bfd"
                stopOpacity={0}
              />
            </linearGradient>
          </defs>

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
            width={55}
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
              `$${Number(value).toFixed(6)}`,
              "Cost",
            ]}
            contentStyle={{
              border: "1px solid #dfe7f1",
              borderRadius: "10px",
              boxShadow:
                "0 10px 30px rgb(23 43 77 / 10%)",
            }}
          />

          <Area
            type="monotone"
            dataKey="cost"
            name="Daily Cost"
            stroke="#246bfd"
            strokeWidth={3}
            fill="url(#costGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}