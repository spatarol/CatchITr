import cv2
import mediapipe as mp
import asyncio
import websockets
import json
import os

# =========================================================
# CONFIG
# =========================================================

CONFIG_FILE = "config.json"

if not os.path.exists(CONFIG_FILE):
    print("❌ File config.json non trovato")
    exit()

try:
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)

    SERVER_IP = config.get("server_ip")
    SERVER_PORT = config.get("server_port")

    SERVER_URI = f"ws://{SERVER_IP}:{SERVER_PORT}"

    print(f"✅ Server configurato: {SERVER_URI}")

except Exception as e:
    print(f"❌ Errore lettura config: {e}")
    exit()

# =========================================================
# MEDIAPIPE
# =========================================================

mp_hands = mp.solutions.hands

hands = mp_hands.Hands(
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

mp_draw = mp.solutions.drawing_utils

# =========================================================
# AREA MONDO
# =========================================================

X_MAX = 8.17
Y_MAX = 4.38

# =========================================================
# SMOOTHING
# =========================================================

prev_x = 0
prev_y = 0

# =========================================================
# CLIENT
# =========================================================

async def hand_tracking_client():

    global prev_x, prev_y

    # ===== APERTURA WEBCAM =====
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ Webcam non trovata")
        return

    print("✅ Webcam aperta")

    try:

        print(f"🔌 Connessione a {SERVER_URI}")

        async with websockets.connect(SERVER_URI) as ws:

            print("✅ Connesso al server")

            while True:

                # =================================================
                # FRAME
                # =================================================

                ret, frame = cap.read()

                if not ret:
                    print("❌ Errore lettura webcam")
                    break

                # Mirror
                frame = cv2.flip(frame, 1)

                h, w, _ = frame.shape

                # =================================================
                # RGB
                # =================================================

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # =================================================
                # HAND TRACKING
                # =================================================

                results = hands.process(frame_rgb)

                if results.multi_hand_landmarks:

                    for handLms in results.multi_hand_landmarks:

                        # Disegna mano
                        mp_draw.draw_landmarks(
                            frame,
                            handLms,
                            mp_hands.HAND_CONNECTIONS
                        )

                        # =============================================
                        # CENTRO MANO
                        # =============================================

                        x_sum = 0
                        y_sum = 0

                        for lm in handLms.landmark:
                            x_sum += lm.x
                            y_sum += lm.y

                        x_avg = x_sum / len(handLms.landmark)
                        y_avg = y_sum / len(handLms.landmark)

                        x_pixel = x_avg * w
                        y_pixel = y_avg * h

                        # Disegna centro
                        cv2.circle(
                            frame,
                            (int(x_pixel), int(y_pixel)),
                            8,
                            (255, 0, 0),
                            -1
                        )

                        # =============================================
                        # NORMALIZZAZIONE
                        # =============================================

                        x_centered = (x_pixel - w / 2) / (w / 2)
                        y_centered = (y_pixel - h / 2) / (h / 2)

                        # Inverti asse Y
                        y_centered = -y_centered

                        # Coordinate mondo
                        x_world = x_centered * X_MAX
                        y_world = y_centered * Y_MAX

                        # =============================================
                        # SMOOTHING
                        # =============================================

                        alpha = 0.7

                        x_world = alpha * prev_x + (1 - alpha) * x_world
                        y_world = alpha * prev_y + (1 - alpha) * y_world

                        prev_x = x_world
                        prev_y = y_world

                        # =============================================
                        # CLICK
                        # =============================================

                        thumb_tip = handLms.landmark[4]
                        middle_tip = handLms.landmark[12]

                        dist = (
                            (middle_tip.x - thumb_tip.x) ** 2 +
                            (middle_tip.y - thumb_tip.y) ** 2
                        ) ** 0.5

                        click = dist < 0.06

                        # =============================================
                        # TESTO
                        # =============================================

                        cv2.putText(
                            frame,
                            f"X: {x_world:.2f}  Y: {y_world:.2f}",
                            (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (0, 255, 0),
                            2
                        )

                        cv2.putText(
                            frame,
                            f"CLICK: {click}",
                            (20, 80),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (0, 0, 255),
                            2
                        )

                        # =============================================
                        # DATI DA INVIARE
                        # =============================================

                        data = {
                            "type": "coordinates",
                            "x": x_world,
                            "y": y_world,
                            "click": click,
                            "thumbX": thumb_tip.x,
                            "thumbY": thumb_tip.y,
                            "middleX": middle_tip.x,
                            "middleY": middle_tip.y
                        }

                        # Invio websocket
                        await ws.send(json.dumps(data))

                # =================================================
                # MOSTRA FRAME
                # =================================================

                cv2.imshow("Hand Tracking Client", frame)

                # =================================================
                # USCITA
                # =================================================

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("👋 Chiusura programma")
                    break

                # =================================================
                # FPS LIMIT
                # =================================================

                await asyncio.sleep(0.016)

    except Exception as e:
        print(f"❌ Errore websocket/server: {e}")

    finally:

        cap.release()
        cv2.destroyAllWindows()

        print("✅ Risorse rilasciate")


# =========================================================
# START
# =========================================================

asyncio.run(hand_tracking_client())