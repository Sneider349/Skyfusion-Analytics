import { useEffect, useState, useRef } from 'react';
import io from 'socket.io-client';

const SOCKET_URL = 'http://localhost:3001';

export function useWebSocket(room = null) {
  const [lastMessage, setLastMessage] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef(null);

  useEffect(() => {
    const socket = io(SOCKET_URL, {
      transports: ['polling', 'websocket'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5
    });

    socketRef.current = socket;

    socketRef.current.on('connect', () => {
      setIsConnected(true);
      if (room) {
        socketRef.current.emit('subscribe', room);
      }
    });

    socketRef.current.on('disconnect', () => {
      setIsConnected(false);
    });

    socketRef.current.on('prediction', (data) => {
      setLastMessage({ type: 'prediction', data });
    });

    socketRef.current.on('alert', (data) => {
      setLastMessage({ type: 'alert', data });
    });

    socketRef.current.on('metrics', (data) => {
      setLastMessage({ type: 'metrics', data });
    });

    return () => {
      socketRef.current?.disconnect();
    };
  }, [room]);

  const emit = (event, data) => {
    socketRef.current?.emit(event, data);
  };

  return { lastMessage, isConnected, emit };
}

export default useWebSocket;
