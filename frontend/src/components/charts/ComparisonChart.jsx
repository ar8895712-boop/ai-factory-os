// frontend/src/components/charts/ComparisonChart.jsx
import React from 'react'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from 'recharts'

export default function ComparisonChart({
  data = [],
  dataKey1 = 'baseline',
  dataKey2 = 'scenario',
  label1 = 'Baseline',
  label2 = 'Scenario',
  unit = '',
  height = 240,
}) {
  if (!data || data.length === 0) {
    return (
      <div
        style={{ height }}
        className="card flex items-center justify-center caption-4 text-text-muted"
      >
        No comparison data available
      </div>
    )
  }

  return (
    <div style={{ height, width: '100%' }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
          <XAxis
            dataKey="name"
            stroke="#6B6B6B"
            tick={{ fill: '#9B9B9B', fontSize: 11 }}
            tickLine={false}
            axisLine={{ stroke: '#272727' }}
          />
          <YAxis
            stroke="#6B6B6B"
            tick={{ fill: '#9B9B9B', fontSize: 11, fontFamily: 'Geist Mono' }}
            tickLine={false}
            axisLine={{ stroke: '#272727' }}
            unit={unit}
          />
          <Tooltip
            content={({ active, payload, label }) => {
              if (active && payload && payload.length) {
                return (
                  <div className="bg-bg-raised border border-border-default p-2.5 rounded-lg shadow-lg">
                    <div className="caption-4 text-white font-medium mb-1">{label}</div>
                    {payload.map((entry, index) => (
                      <div key={index} className="caption-5 mono flex justify-between gap-4 py-0.5">
                        <span className="text-text-muted">{entry.name}:</span>
                        <span className="text-white font-medium">
                          {Number(entry.value).toLocaleString('en-IN')} {unit}
                        </span>
                      </div>
                    ))}
                  </div>
                )
              }
              return null
            }}
          />
          <Legend
            wrapperStyle={{ paddingTop: 8, fontSize: 11, color: '#9B9B9B' }}
          />
          <Bar dataKey={dataKey1} name={label1} fill="#6B6B6B" radius={[4, 4, 0, 0]} />
          <Bar dataKey={dataKey2} name={label2} fill="#FFFFFF" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

