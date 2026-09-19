using TMPro;
using UnityEngine;

public class GameOverUI : MonoBehaviour
{
    public TextMeshProUGUI punteggioText;
    public TextMeshProUGUI tempoText;

    void Start()
    {
        punteggioText.text = "Punteggio: " + GameManager2.punteggio;
        tempoText.text = "Tempo medio: " + GameManager2.tempoMedio.ToString("F2") + " s";
    }
}