import asyncio
import websockets
import json
import random

async def invia_coordinate(websocket):
    """Invia coordinate casuali al client ogni 2-3 secondi"""
    print(f"Client connesso: {websocket.remote_address}")
    
    try:
        while True:
            # Genera coordinate casuali
           
            raggio = random.randint(5, 20)
            x = random.randint(raggio+1, (640 - raggio - 1))
            y = random.randint(raggio+1, (480 - raggio - 1))
            
            # Genera colore casuale (formato esadecimale)
            colore = "#{:06x}".format(random.randint(0, 0xFFFFFF))
            
            # Crea messaggio JSON
            messaggio = {
                "x": x,
                "y": y,
                "raggio": raggio,
                "colore": colore
            }
            
            # Invia al client
            await websocket.send(json.dumps(messaggio))
            print(f"Inviato: {messaggio}")
            
            # Attendi 2-3 secondi casuali
            await asyncio.sleep(random.uniform(2, 3))
            
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnesso")

async def main():
    """Avvia il server WebSocket"""
    print("Server WebSocket avviato su ws://localhost:8765")
    async with websockets.serve(invia_coordinate, "localhost", 8765):
        await asyncio.Future()  # Mantiene il server attivo

if __name__ == "__main__":
    asyncio.run(main())