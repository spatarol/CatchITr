using System;
using System.Collections;
using System.IO;
using System.Globalization;
using UnityEngine;
using TMPro;
using UnityEngine.SceneManagement;

public class Target_move : MonoBehaviour
{
    [Header("Statistiche Target")]
    public int score = 0;
    public TextMeshProUGUI punteggioText;
    public TextMeshProUGUI tempoMText;
    public TextMeshProUGUI tempoPartitaText;
    private float tempoRimanente;

    [Header("Effetti")]
    public GameObject effettoCoriandoli;
    public TextMeshProUGUI countdownText;

    [Header("Durata Partita")]
    public float durataPartita = 60f; // secondi

    private bool giocoFinito = false;
    private bool contoAllaRovesciaAttivo = true;

    [Header("Audio")]
    public AudioClip hitSound;
    private AudioSource audioSource;

    [Header("Movimento Automatico")]
    public float tempoAttesa = 3f;

    [Header("Limiti Area di Spostamento")]
    public float minX = -9.83f;
    public float maxX = 9.83f;
    public float minY = -3.9f;
    public float maxY = 3.9f;

    public bool showArea = false;
    public GameObject squareArea;

    [Header("Timer Reazione")]
    private bool timerAttivo = false;
    private float tempoInizio;
    private float tempoTrascorso;

    private Coroutine movimentoRoutine;
    private int nBersagli = 0;
    private float tempoTot = 0.0f;

    private bool mouseDentro = false;


    void Start()
    {
        CoordinateTarget();

        tempoRimanente = durataPartita;

        audioSource = GetComponent<AudioSource>();

        AggiornaUI();

        StartCoroutine(ContoAllaRovescia());
    }

    IEnumerator ContoAllaRovescia()
    {
        countdownText.gameObject.SetActive(true);

        countdownText.text = "     3";
        yield return new WaitForSeconds(1f);

        countdownText.text = "     2";
        yield return new WaitForSeconds(1f);

        countdownText.text = "     1";
        yield return new WaitForSeconds(1f);

        countdownText.text = "START";
        yield return new WaitForSeconds(2f);

        countdownText.gameObject.SetActive(false);

        // Il countdown è terminato
        contoAllaRovesciaAttivo = false;

        // Da qui parte realmente il gioco
        SpostaSuPosizioneCasuale();

        movimentoRoutine = StartCoroutine(SpostaRipetiRoutine());

        StartCoroutine(TimerPartita());
    }
    void CoordinateTarget()
    {
        string targetPath = Path.GetFullPath(
            Path.Combine(Application.dataPath, "../Target.txt")
        );


        if (!File.Exists(targetPath))
        {
            Debug.LogError("❌ File Target.txt non trovato");
            return;
        }


        try
        {
            foreach (string line in File.ReadAllLines(targetPath))
            {
                string[] parts = line.Split('=');


                if (parts.Length != 2)
                    continue;


                string key = parts[0].Trim();


                float value = float.Parse(
                    parts[1].Trim(),
                    CultureInfo.InvariantCulture
                );


                switch (key)
                {
                    case "minX":
                        minX = value;
                        break;

                    case "maxX":
                        maxX = value;
                        break;

                    case "minY":
                        minY = value;
                        break;

                    case "maxY":
                        maxY = value;
                        break;

                    case "limits":
                        showArea = Mathf.Abs(value) > 0.01f;
                        break;

                    case "gameTime":
                        durataPartita = value;
                        break;
                }
            }


            if (showArea && squareArea != null)
            {
                float larghezza = maxX - minX;
                float altezza = maxY - minY;


                squareArea.transform.localScale =
                    new Vector3(
                        larghezza,
                        altezza,
                        1f
                    );


                squareArea.transform.position =
                    new Vector3(
                        (minX + maxX) / 2f,
                        (minY + maxY) / 2f,
                        squareArea.transform.position.z
                    );


                squareArea.SetActive(true);
            }


            Debug.Log(
                $"✅ Coordinate caricate: X({minX}, {maxX}) Y({minY}, {maxY})"
            );
        }
        catch (Exception e)
        {
            Debug.LogError(
                $"❌ Errore lettura Target.txt: {e.Message}"
            );
        }
    }


    IEnumerator SpostaRipetiRoutine()
    {
        while (true)
        {
            yield return new WaitForSeconds(tempoAttesa);
            FermaTimer();
            SpostaSuPosizioneCasuale();
        }
    }


    void OnTriggerEnter2D(Collider2D other)
    {
        if (!other.CompareTag("mouse"))
            return;

        if (GameSettings.useClick)
        {
            mouseDentro = true;
        }
        else
        {
            HandleHit();
        }
    }

    void OnTriggerExit2D(Collider2D other)
    {
        if (other.CompareTag("mouse"))
        {
            mouseDentro = false;
        }
    }

    void HandleHit()
    {
if (contoAllaRovesciaAttivo || giocoFinito)
    return;

        FermaTimer();


        score++;

        AggiornaUI();



        if (hitSound != null && audioSource != null)
        {
            audioSource.PlayOneShot(hitSound);

            StartCoroutine(
                StopSoundAfterTime(0.15f)
            );
        }



        if (effettoCoriandoli != null)
        {
            GameObject effetto =
                Instantiate(
                    effettoCoriandoli,
                    transform.position,
                    Quaternion.identity
                );


            Destroy(effetto, 2f);
        }



        if (movimentoRoutine != null)
        {
            StopCoroutine(movimentoRoutine);
        }


        StartCoroutine(HitDelayRoutine());
    }



    IEnumerator StopSoundAfterTime(float time)
    {
        yield return new WaitForSeconds(time);

        if (audioSource != null)
            audioSource.Stop();
    }



    IEnumerator HitDelayRoutine()
    {
        transform.position = new Vector3(999, 999, transform.position.z);

        yield return new WaitForSeconds(1f);

        if (giocoFinito)
            yield break;

        SpostaSuPosizioneCasuale();

        movimentoRoutine = StartCoroutine(SpostaRipetiRoutine());
    }



    void SpostaSuPosizioneCasuale()
    {
        nBersagli++;
        float randomX =
            UnityEngine.Random.Range(
                minX,
                maxX
            );


        float randomY =
            UnityEngine.Random.Range(
                minY,
                maxY
            );


        transform.position =
            new Vector3(
                randomX,
                randomY,
                transform.position.z
            );


        AvviaTimer();


        Debug.Log(
            $"Spawn -> X:{randomX} Y:{randomY}"
        );
    }


    void AvviaTimer()
    {
        timerAttivo = true;
        tempoInizio = Time.time;

        Debug.Log("Timer ripartito");
    }


    void FermaTimer()
    {
        if (timerAttivo)
        {
            tempoTrascorso =
                Time.time - tempoInizio;

            timerAttivo = false;

            tempoTot += tempoTrascorso;
            Debug.Log(
                $"Tempo reazione: {tempoTrascorso:F3} secondi"
            );
            Debug.Log(
                "tempo medio = " + tempoTot / nBersagli
            );
        }
    }



    void AggiornaUI()
    {
        if (punteggioText != null)
        {
            punteggioText.text =
                "Punteggio: " + score;
        }
        if (tempoMText != null)
        {
            if (nBersagli > 0)
                tempoMText.text = "Tempo Medio: " + tempoTot / nBersagli;

        }
    }

    void FineGioco()
    {
        if (giocoFinito)
            return;

        giocoFinito = true;

        FermaTimer();
        AggiornaUI();

        if (movimentoRoutine != null)
            StopCoroutine(movimentoRoutine);

        SalvaRisultato();

        Debug.Log("PARTITA TERMINATA!");

        GameManager2.punteggio = score;
        GameManager2.bersagliPresi = score;
        GameManager2.tempoMedio = (nBersagli > 0) ? tempoTot / nBersagli : 0f;


        SceneManager.LoadScene("GameOver");
    }

    IEnumerator TimerPartita()
    {
        yield return new WaitForSeconds(durataPartita);

        FineGioco();
    }

    void SalvaRisultato()
    {
        string filePath = Path.Combine(Application.dataPath, "../Risultati.txt");

        float tempoMedio = (nBersagli > 0) ? tempoTot / nBersagli : 0f;

        string riga =
            DateTime.Now.ToString("dd/MM/yyyy HH:mm:ss") +
            "   Punteggio: " + score +
            "   Tempo Medio: " + tempoMedio.ToString("F3", CultureInfo.InvariantCulture);

        File.AppendAllText(filePath, riga + Environment.NewLine);

        Debug.Log("Risultato salvato in: " + filePath);
    }

    void Update()
    {
        if (contoAllaRovesciaAttivo || giocoFinito)
            return;

        tempoRimanente -= Time.deltaTime;

        if (tempoRimanente < 0)
            tempoRimanente = 0;

        if (tempoPartitaText != null)
        {
            tempoPartitaText.text =
                "Tempo: " +
                tempoRimanente.ToString("F1") +
                " s";
        }

        // Modalità Click
        if (GameSettings.useClick)
        {
            if (mouseDentro && Mouse.HandClosed)
            {
                HandleHit();
                mouseDentro = false;
            }
        }
    }

}