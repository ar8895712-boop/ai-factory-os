// frontend/src/components/charts/AnomalyTrendChart.jsx
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

export default function AnomalyTrendChart({
  data = [],
  threshold = 0.75,
  height = 240,
}) {
  if (!data || data.length === 0) {
    return (
      <div
        style={{ height }}
        className="card flex items-center justify-center caption-4 text-text-muted"
      >
        No anomaly trend data available for current window
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
            domain={[0, 1]}
            stroke="#6B6B6B"
            tick={{ fill: '#9B9B9B', fontSize: 11, fontFamily: 'Geist Mono' }}
            tickLine={false}
            axisLine={{ stroke: '#272727' }}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const item = payload[0].payload
                return (
                  <div className="bg-bg-raised border border-border-default p-2.5 rounded-lg shadow-lg">
                    <div className="caption-5 text-text-muted mono">Cycle: {item.cycle}</div>
                    <div className="title-5 text-white mono mt-0.5">
                      Score: <span className="font-semibold text-status-critical">{Number(item.score).toFixed(2)}</span>
                    </div>
                  </div>
                )
              }
              return null
            }}
          />
          <ReferenceLine
            y={threshold}
            stroke="#f87171"
            strokeDasharray="4 4"
            label={{ value: 'Critical (0.75)', fill: '#f87171', fontSize: 10, position: 'insideTopRight' }}
          />
          <Line
            type="monotone"
            dataKey="score"
            stroke="#FFFFFF"
            strokeWidth={2}
            dot={{ r: 2, fill: '#FFFFFF' }}
            activeDot={{ r: 4, fill: '#f87171' }}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

