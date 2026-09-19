import asyncio
import json
import websockets

clients = set()

# ✅ GLOBALI
loop = None
ws_server = None


async def handler(websocket):
    clients.add(websocket)
    print("Client connesso")

    try:
        async for msg in websocket:
            data = json.loads(msg)
            print("Messaggio ricevuto:", data)

            if "x" in data and "y" in data:
                x = data["x"]
                y = data["y"]
                click = data.get("click", False)

                print(f"Coordinate: {x}, {y} | Click: {click}")

                for client in clients:
                    if client != websocket:
                        # 🔥 CAMBIATO SOLO QUESTO
                        await client.send(json.dumps(data))

    except websockets.exceptions.ConnectionClosed:
        print("Client disconnesso")

    finally:
        clients.discard(websocket)


async def main():
    global ws_server
    ws_server = await websockets.serve(handler, "0.0.0.0", 8765)
    print("Server avviato su ws://0.0.0.0:8765")

    try:
        await asyncio.Future()  # resta attivo
    except asyncio.CancelledError:
        pass


# ✅ START SERVER
def start_ws_server():
    global loop

    if loop is not None:
        print("Server già in esecuzione")
        return

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(main())
    except Exception as e:
        print("Errore WS:", e)
    finally:
        loop = None


# ✅ STOP SERVER
def stop_ws_server():
    global loop, ws_server

    if loop and ws_server:

        async def shutdown():
            ws_server.close()
            await ws_server.wait_closed()

            # cancella tutto
            tasks = [t for t in asyncio.all_tasks(loop) if not t.done()]
            for task in tasks:
                task.cancel()

        future = asyncio.run_coroutine_threadsafe(shutdown(), loop)

        try:
            future.result(timeout=3)
        except:
            pass

        loop.call_soon_threadsafe(loop.stop)

        ws_server = None
        loop = None

        print("Server WebSocket chiuso correttamente")

