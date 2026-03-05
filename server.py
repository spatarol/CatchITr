import cv2
import mediapipe as mp
import random

mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

circle_radius = 50

def new_circle_position(frame):
    h, w, _ = frame.shape
    x = random.randint(circle_radius, w - circle_radius)
    y = random.randint(circle_radius, h - circle_radius)
    return x, y

# inizializzazione
ret, frame = cap.read()
frame = cv2.flip(frame, 1)  # rimuove effetto specchio
circle_x, circle_y = new_circle_position(frame)
circle_color = (0, 0, 255)  # rosso

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)  # rimuove effetto specchio

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    presa = False

    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, handLms, mp_hands.HAND_CONNECTIONS)

            x_thumb = int(handLms.landmark[mp_hands.HandLandmark.THUMB_TIP].x * frame.shape[1])
            y_thumb = int(handLms.landmark[mp_hands.HandLandmark.THUMB_TIP].y * frame.shape[0])
            x_index = int(handLms.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].x * frame.shape[1])
            y_index = int(handLms.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y * frame.shape[0])

            if ((x_thumb - circle_x)**2 + (y_thumb - circle_y)**2) < circle_radius**2 or \
               ((x_index - circle_x)**2 + (y_index - circle_y)**2) < circle_radius**2:
                presa = True

    if presa:
        circle_color = (0, 255, 0)  # verde
        circle_x, circle_y = new_circle_position(frame)
    else:
        circle_color = (0, 0, 255)  # rosso

    cv2.circle(frame, (circle_x, circle_y), circle_radius, circle_color, -1)
    cv2.imshow("Hand Game", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()