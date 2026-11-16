// ==============================================================
// frontend/src/hooks/useWebSocket.js — Live Telemetry Hook
// ==============================================================
import { useEffect, useRef, useState } from 'react'

export function useWebSocket(url = '/ws/live') {
  const [isConnected, setIsConnected] = useState(false)
  const [telemetry, setTelemetry] = useState(null)
  const [lastMessageTime, setLastMessageTime] = useState(null)
  const wsRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)

  useEffect(() => {
    let isMounted = true

    function connect() {
      // Determine protocol: ws or wss
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = window.location.host
      // Use proxy or direct host
      const wsUrl = url.startsWith('ws') ? url : `${protocol}//${host}${url}`

      try {
        const ws = new WebSocket(wsUrl)
        wsRef.current = ws

        ws.onopen = () => {
          if (!isMounted) return
          setIsConnected(true)
          // Heartbeat ping every 15s
          const pingInterval = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send('ping')
            }
          }, 15000)
          ws._pingInterval = pingInterval
        }

        ws.onmessage = (event) => {
          if (!isMounted) return
          if (event.data === 'pong') return
          try {
            const data = JSON.parse(event.data)
            if (data.type === 'telemetry') {
              setTelemetry(data)
              setLastMessageTime(new Date())
            }
          } catch (e) {
            console.error('Failed to parse WebSocket message:', e)
          }
        }

        ws.onclose = () => {
          if (!isMounted) return
          setIsConnected(false)
          clearInterval(ws._pingInterval)
          // Reconnect after 2 seconds
          reconnectTimeoutRef.current = setTimeout(connect, 2000)
        }

        ws.onerror = () => {
          ws.close()
        }
      } catch (e) {
        console.error('WebSocket connection error:', e)
        reconnectTimeoutRef.current = setTimeout(connect, 2000)
      }
    }

    connect()

    return () => {
      isMounted = false
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current)
      if (wsRef.current) {
        clearInterval(wsRef.current._pingInterval)
        wsRef.current.close()
      }
    }
  }, [url])

  return { isConnected, telemetry, lastMessageTime }
}

