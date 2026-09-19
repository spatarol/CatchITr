using UnityEngine;
using UnityEngine.SceneManagement;

public class OptionsMenu : MonoBehaviour
{
    public GameObject optionsPanel;

    public void OpenOptions()
    {
        optionsPanel.SetActive(true);
    }

    public void StartGame()
    {
        GameSettings.useClick = true;
        SceneManager.LoadScene("Game");
    }

    public void ClickMode()
    {
        GameSettings.useClick = true;
        SceneManager.LoadScene("Game");
    }

    public void NoClickMode()
    {
        GameSettings.useClick = false;
        SceneManager.LoadScene("Game");
    }
}