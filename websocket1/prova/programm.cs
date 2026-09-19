using System;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace ScoreSender
{
    class Program
    {
        static int score = 0;
        static int increment = 10;

        static async Task Main(string[] args)
        {
            Console.WriteLine("Simulazione punteggio in corso...");
            
            // Incrementa il punteggio ogni secondo per 10 secondi
            for (int i = 0; i < 10; i++)
            {
                score += increment;
                Console.WriteLine($"Punteggio attuale: {score}");
                await Task.Delay(1000);
            }

            // Invia punteggio a Flask
            await SendScore(score);
            Console.WriteLine("Punteggio inviato. Premere un tasto per uscire.");
            Console.ReadKey();
        }

        static async Task SendScore(int finalScore)
        {
            var httpClient = new HttpClient();
            var url = "http://localhost:3020/api/score"; // Assicurati che figo.py sia in esecuzione

            var payload = new { score = finalScore };
            var json = JsonSerializer.Serialize(payload);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            try
            {
                var response = await httpClient.PostAsync(url, content);
                if (response.IsSuccessStatusCode)
                {
                    Console.WriteLine("Punteggio inviato correttamente al server.");
                }
                else
                {
                    Console.WriteLine($"Errore invio punteggio: {response.StatusCode}");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Errore connessione al server: {ex.Message}");
            }
        }
    }
}