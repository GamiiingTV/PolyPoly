import { useState, useEffect, useRef, useCallback } from 'react'
import type { WsMessage } from '../types'

export function useWebSocket(onMessage: (msg: WsMessage) => void) {
  const [connected, setConnected] = useState(false)
  const [retries, setRetries] = useState(0)
  const wsRef = useRef<WebSocket | null>(null)
  const onMsgRef = useRef(onMessage)
  const retryRef = useRef(0)
  const timerRef = useRef<ReturnType<typeof setTimeout>>()

  onMsgRef.current = onMessage

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return
    const ws = new WebSocket('ws://localhost:8000/ws/dashboard')
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      retryRef.current = 0
      setRetries(0)
    }

    ws.onmessage = (e) => {
      try {
        onMsgRef.current(JSON.parse(e.data) as WsMessage)
      } catch {
        // ignore malformed messages
      }
    }

    ws.onclose = () => {
      setConnected(false)
      wsRef.current = null
      retryRef.current += 1
      setRetries(retryRef.current)
      const delay = Math.min(3000 * retryRef.current, 15000)
      timerRef.current = setTimeout(connect, delay)
    }

    ws.onerror = () => {
      ws.close()
    }
  }, [])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(timerRef.current)
      wsRef.current?.close()
    }
  }, [connect])

  return { connected, retries }
}
