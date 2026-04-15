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

    bool giaAttivato = false;
    bool isClicking = false;

    async void Start()
    {
        websocket = new ClientWebSocket();
        Uri serverUri = new Uri("ws://192.168.103.49:8765");

        try
        {
            await websocket.ConnectAsync(serverUri, CancellationToken.None);
            _ = RiceviCoordinate();
        }
        catch (Exception e)
        {
            Debug.LogError(e.Message);
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
                    targetPosition = new Vector3(msg.x, msg.y, transform.position.z);
                    isClicking = msg.click;
                }
            }
        }
    }

    void Update()
    {
        // movimento mano
        transform.position = Vector3.Lerp(
            transform.position,
            targetPosition,
            10f * Time.deltaTime
        );

        // raycast UI
        PointerEventData pointerData = new PointerEventData(EventSystem.current);
        pointerData.position = RectTransformUtility.WorldToScreenPoint(cam, transform.position);

        List<RaycastResult> results = new List<RaycastResult>();
        EventSystem.current.RaycastAll(pointerData, results);

        bool sopraBottone = false;

        foreach (var result in results)
        {
            if (result.gameObject.name == "StartButton")
            {
                sopraBottone = true;

                if (isClicking && !giaAttivato)
                {
                    Debug.Log("CLICK!");

                    Button btn = result.gameObject.GetComponent<Button>();
                    if (btn != null)
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
        if (websocket != null && websocket.State == WebSocketState.Open)
        {
            await websocket.CloseAsync(
                WebSocketCloseStatus.NormalClosure,
                "Chiudo",
                CancellationToken.None
            );
        }
    }
}