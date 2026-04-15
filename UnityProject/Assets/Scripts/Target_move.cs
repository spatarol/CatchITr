using System.Collections;
using UnityEngine;
using TMPro;

public class Target_move : MonoBehaviour
{
    [Header("Statistiche Target")]
    public int score = 0;
    public TextMeshProUGUI punteggioText;

    [Header("Movimento Automatico")]
    public float tempoAttesa = 3f;

    [Header("Limiti Area di Spostamento")]
    public float minX = -9.83f;
    public float maxX = 9.83f;
    public float minY = -3.9f;
    public float maxY = 3.9f;

    private Coroutine movimentoRoutine;

    void Start()
    {
        SpostaSuPosizioneCasuale();
        movimentoRoutine = StartCoroutine(SpostaRipetiRoutine());
        AggiornaUI();
    }

    private IEnumerator SpostaRipetiRoutine()
    {
        while (true)
        {
            yield return new WaitForSeconds(tempoAttesa);
            SpostaSuPosizioneCasuale();
        }
    }

    void OnTriggerEnter2D(Collider2D other)
    {
        if (other.gameObject.CompareTag("mouse"))
        {
            HandleHit();
        }
    }

    void HandleHit()
    {
        score++;
        AggiornaUI();

        if (movimentoRoutine != null)
            StopCoroutine(movimentoRoutine);

        StartCoroutine(HitDelayRoutine());
    }

    private IEnumerator HitDelayRoutine()
    {
        // nasconde temporaneamente
        transform.position = new Vector3(999, 999, transform.position.z);

        yield return new WaitForSeconds(1f);

        SpostaSuPosizioneCasuale();
        movimentoRoutine = StartCoroutine(SpostaRipetiRoutine());
    }

    void SpostaSuPosizioneCasuale()
    {
        float randomX = Random.Range(minX, maxX);
        float randomY = Random.Range(minY, maxY);

        // 👇 FIX IMPORTANTE: mantiene la Z originale
        transform.position = new Vector3(randomX, randomY, transform.position.z);

        // 👇 DEBUG (puoi toglierlo dopo)
        Debug.Log("Spawn -> X: " + randomX + " Y: " + randomY);
    }

    void AggiornaUI()
    {
        punteggioText.text = "Punteggio: " + score;
    }
}