// frontend/src/components/charts/HealthTrendChart.jsx
import React from 'react'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
} from 'recharts'

export default function HealthTrendChart({
  data = [],
  warningThreshold = 60,
  criticalThreshold = 35,
  height = 260,
}) {
  if (!data || data.length === 0) {
    return (
      <div
        style={{ height }}
        className="card flex items-center justify-center caption-4 text-text-muted"
      >
        No health score history recorded
      </div>
    )
  }

  return (
    <div style={{ height, width: '100%' }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <XAxis
            dataKey="cycle"
            stroke="#6B6B6B"
            tick={{ fill: '#9B9B9B', fontSize: 11, fontFamily: 'Geist Mono' }}
            tickLine={false}
            axisLine={{ stroke: '#272727' }}
            unit=" cyc"
          />
          <YAxis
            domain={[0, 100]}
            stroke="#6B6B6B"
            tick={{ fill: '#9B9B9B', fontSize: 11, fontFamily: 'Geist Mono' }}
            tickLine={false}
            axisLine={{ stroke: '#272727' }}
            unit="%"
          />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const item = payload[0].payload
                return (
                  <div className="bg-bg-raised border border-border-default p-2.5 rounded-lg shadow-lg">
                    <div className="caption-5 text-text-muted mono">Cycle: {item.cycle}</div>
                    <div className="title-5 text-white mono mt-0.5">
                      Health: <span className="font-semibold text-status-healthy">{Number(item.health).toFixed(1)}%</span>
                    </div>
                  </div>
                )
              }
              return null
            }}
          />
          <ReferenceLine
            y={warningThreshold}
            stroke="#fbbf24"
            strokeDasharray="3 3"
            label={{ value: 'Warning (60%)', fill: '#fbbf24', fontSize: 10, position: 'insideTopRight' }}
          />
          <ReferenceLine
            y={criticalThreshold}
            stroke="#f87171"
            strokeDasharray="3 3"
            label={{ value: 'Critical (35%)', fill: '#f87171', fontSize: 10, position: 'insideTopRight' }}
          />
          <Line
            type="monotone"
            dataKey="health"
            stroke="#4ade80"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: '#FFFFFF' }}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

