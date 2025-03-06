#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste para verificar se o módulo pepperpy.core.events está funcionando corretamente."""

import sys
import asyncio
from typing import List, Any

async def test_events():
    """Testa se o módulo pepperpy.core.events está funcionando corretamente."""
    try:
        from pepperpy.core.events import EventType, EventBus, get_event_bus
        
        # Testar EventType
        assert EventType.INITIALIZE is not None
        assert EventType.PROCESS_START is not None
        
        # Testar EventBus
        event_bus = EventBus()
        assert event_bus is not None
        
        # Testar get_event_bus
        singleton_bus = get_event_bus()
        assert singleton_bus is not None
        
        # Testar subscribe e publish
        events_received: List[Any] = []
        
        async def event_handler(data: Any = None):
            events_received.append(data)
        
        event_bus.subscribe(EventType.INITIALIZE, event_handler)
        await event_bus.publish(EventType.INITIALIZE, {"component": "test"})
        
        assert len(events_received) == 1
        assert events_received[0]["component"] == "test"
        
        # Testar unsubscribe
        event_bus.unsubscribe(EventType.INITIALIZE, event_handler)
        await event_bus.publish(EventType.INITIALIZE, {"component": "test2"})
        
        assert len(events_received) == 1  # Não deve ter recebido o segundo evento
        
        print("Teste de eventos concluído com sucesso!")
        return True
    except Exception as e:
        print(f"Erro ao testar eventos: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_events())
    sys.exit(0 if success else 1) 