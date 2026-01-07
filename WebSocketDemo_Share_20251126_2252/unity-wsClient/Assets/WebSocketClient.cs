

using UnityEngine;
using UnityEngine.UI; // Aggiunto per Image
using NativeWebSocket;
using System;

// Classe per deserializzare il messaggio JSON
[Serializable]
public class CoordinataMessaggio
{
    public int x;
    public int y;
    public int raggio;
    public string colore;
}

public class WebSocketClient : MonoBehaviour
{
    private WebSocket websocket;

    // Prefab del cerchio (assegnalo nell'Inspector)
    public GameObject cerchioPrefab;

    // Canvas dove disegnare i cerchi
    public Canvas canvas;

    async void Start()
    {
        // Connetti al server WebSocket
        websocket = new WebSocket("ws://localhost:8765");

        // Evento: quando arriva un messaggio
        websocket.OnMessage += (bytes) =>
        {
            // Converti i bytes in stringa
            string messaggioJson = System.Text.Encoding.UTF8.GetString(bytes);
            Debug.Log("Ricevuto: " + messaggioJson);

            // Deserializza il JSON
            CoordinataMessaggio msg = JsonUtility.FromJson<CoordinataMessaggio>(messaggioJson);

            // Disegna il cerchio (deve essere fatto nel thread principale)
            DisegnaCerchio(msg.x, msg.y, msg.raggio, msg.colore);
        };

        // Eventi di connessione
        websocket.OnOpen += () => Debug.Log("Connesso al server!");
        websocket.OnError += (e) => Debug.Log("Errore: " + e);
        websocket.OnClose += (e) => Debug.Log("Connessione chiusa");

        // Connetti
        await websocket.Connect();
    }

    void Update()
    {
        // Necessario per processare i messaggi in arrivo
#if !UNITY_WEBGL || UNITY_EDITOR
        if (websocket != null)
        {
            websocket.DispatchMessageQueue();
        }
#endif
    }

    void DisegnaCerchio(int x, int y, int raggio, string coloreHex)
    {
        // Crea un nuovo cerchio
        GameObject cerchio = Instantiate(cerchioPrefab, canvas.transform);

        // Imposta posizione (converti da coordinate schermo a Canvas)
        RectTransform rect = cerchio.GetComponent<RectTransform>();
        rect.anchoredPosition = new Vector2(x - 320, y - 240); // Centra rispetto a 640x480

        // Imposta dimensione (diametro = raggio * 2)
        rect.sizeDelta = new Vector2(raggio * 2, raggio * 2);

        // Imposta colore
        UnityEngine.UI.Image img = cerchio.GetComponent<UnityEngine.UI.Image>();
        if (img != null && ColorUtility.TryParseHtmlString(coloreHex, out Color colore))
        {
            img.color = colore;
        }
    }

    async void OnApplicationQuit()
    {
        // Chiudi la connessione quando l'app si chiude
        if (websocket != null)
        {
            await websocket.Close();
        }
    }
}