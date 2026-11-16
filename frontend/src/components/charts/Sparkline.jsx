// frontend/src/components/charts/Sparkline.jsx
import React from 'react'
import { ResponsiveContainer, LineChart, Line } from 'recharts'

export default function Sparkline({
  data = [],
  dataKey = 'health',
  status = 'healthy',
  height = 36,
  width = '100%',
}) {
  if (!data || data.length === 0) {
    return <div className="h-9 flex items-center justify-center caption-5 text-text-muted">No trend</div>
  }

  const strokeColor = {
    healthy:  '#4ade80',
    warning:  '#fbbf24',
    critical: '#f87171',
    info:     '#60a5fa',
  }[status] || '#4ade80'

  return (
    <div style={{ height, width }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <Line
            type="monotone"
            dataKey={dataKey}
            stroke={strokeColor}
            strokeWidth={1.75}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

