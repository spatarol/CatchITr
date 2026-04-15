import cv2
import mediapipe as mp
import asyncio
import websockets
import json

mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_draw = mp.solutions.drawing_utils

X_MAX = 8.17
Y_MAX = 4.38

SERVER_URI = "ws://192.168.103.49:8765"

async def hand_tracking_client():

    cap = cv2.VideoCapture(0)

    async with websockets.connect(SERVER_URI) as ws:
        print("Connesso al server")

        while True:

            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(frame_rgb)

            if results.multi_hand_landmarks:

                for handLms in results.multi_hand_landmarks:

                    # MEDIA POSIZIONE MANO
                    x_sum = 0
                    y_sum = 0

                    for lm in handLms.landmark:
                        x_sum += lm.x
                        y_sum += lm.y

                    x_avg = x_sum / len(handLms.landmark)
                    y_avg = y_sum / len(handLms.landmark)

                    x_pixel = x_avg * w
                    y_pixel = y_avg * h

                    cv2.circle(frame, (int(x_pixel), int(y_pixel)), 8, (255, 0, 0), -1)

                    # NORMALIZZAZIONE
                    x_centered = (x_pixel - w/2) / (w/2)
                    y_centered = (y_pixel - h/2) / (h/2)

                    y_centered = -y_centered

                    x_world = x_centered * X_MAX
                    y_world = y_centered * Y_MAX

                    # 👇 CLICK (pollice + indice)
                    index_tip = handLms.landmark[8]
                    thumb_tip = handLms.landmark[4]

                    dist = ((index_tip.x - thumb_tip.x)**2 + (index_tip.y - thumb_tip.y)**2)**0.5
                    click = dist < 0.05

                    # INVIO DATI
                    await ws.send(json.dumps({
                        "type": "coordinates",
                        "x": x_world,
                        "y": y_world,
                        "click": click
                    }))

            cv2.imshow("Hand Tracking Client", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            await asyncio.sleep(0.016)

    cap.release()
    cv2.destroyAllWindows()

asyncio.run(hand_tracking_client())





