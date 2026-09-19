
using UnityEngine;
using System;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.IO;
using UnityEngine.EventSystems;
using System.Collections.Generic;
using UnityEngine.UI;

[Serializable]
public class CoordinateMessage
{
    public string type;
    public float x;
    public float y;
    public bool click;
}

public class Mouse : MonoBehaviour
{
    ClientWebSocket websocket;
    Vector3 targetPosition;

    public Camera cam;

    // Sprite mano
    public GameObject openHand;
    public GameObject closedHand;

    bool giaAttivato = false;
    bool isClicking = false;

    public static bool HandClosed = false;

    async void Start()
    {
        websocket = new ClientWebSocket();

        try
        {
            // Percorso del file config.txt
            string configPath = Path.Combine(Application.dataPath, "../config.txt");

            // Controlla se esiste
            if (!File.Exists(configPath))
            {
                Debug.LogError("config.txt non trovato!");
                return;
            }

            // Legge IP/server dal file
            string serverAddress = File.ReadAllText(configPath).Trim();

            Debug.Log("Connessione a: " + serverAddress);

            Uri serverUri = new Uri(serverAddress);

            // Connessione websocket
            await websocket.ConnectAsync(serverUri, CancellationToken.None);

            // Avvia ricezione dati
            _ = RiceviCoordinate();
        }
        catch (Exception e)
        {
            Debug.LogError("Errore websocket/config: " + e.Message);
        }
    }

    async Task RiceviCoordinate()
    {
        var buffer = new byte[1024];

        while (websocket.State == WebSocketState.Open)
        {
            using (MemoryStream ms = new MemoryStream())
            {
                WebSocketReceiveResult result;

                do
                {
                    result = await websocket.ReceiveAsync(
                        new ArraySegment<byte>(buffer),
                        CancellationToken.None
                    );

                    ms.Write(buffer, 0, result.Count);

                } while (!result.EndOfMessage);

                string json = Encoding.UTF8.GetString(ms.ToArray());

                CoordinateMessage msg = JsonUtility.FromJson<CoordinateMessage>(json);

                if (msg.type == "coordinates")
                {
                    targetPosition = new Vector3(
                        msg.x,
                        msg.y,
                        transform.position.z
                    );

                    isClicking = msg.click;
                }
            }
        }
    }

    void Update()
    {
        // Salva lo stato della mano
        HandClosed = isClicking;

        // Movimento fluido della mano
        transform.position = Vector3.Lerp(
            transform.position,
            targetPosition,
            10f * Time.deltaTime
        );

        // Cambio sprite mano
        if (isClicking)
        {
            openHand.SetActive(false);
            closedHand.SetActive(true);
        }
        else
        {
            openHand.SetActive(true);
            closedHand.SetActive(false);
        }

        // Raycast UI
        PointerEventData pointerData =
            new PointerEventData(EventSystem.current);

        pointerData.position =
            RectTransformUtility.WorldToScreenPoint(
                cam,
                transform.position
            );

        List<RaycastResult> results =
            new List<RaycastResult>();

        EventSystem.current.RaycastAll(pointerData, results);

        bool sopraBottone = false;

        foreach (var result in results)
        {
            Button btn =
                result.gameObject.GetComponent<Button>();

            if (btn != null)
            {
                sopraBottone = true;

                if (isClicking && !giaAttivato)
                {
                    Debug.Log("CLICK!");

                    btn.onClick.Invoke();

                    giaAttivato = true;
                }
            }
        }

        if (!sopraBottone || !isClicking)
        {
            giaAttivato = false;
        }
    }

    async void OnApplicationQuit()
    {
        if (websocket != null &&
            websocket.State == WebSocketState.Open)
        {
            await websocket.CloseAsync(
                WebSocketCloseStatus.NormalClosure,
                "Chiudo",
                CancellationToken.None
            );
        }
    }
}