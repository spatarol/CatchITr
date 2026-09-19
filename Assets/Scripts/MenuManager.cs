using UnityEngine;

public class OptionsManager : MonoBehaviour
{
    public GameObject optionsPanel;

    public void OpenOptions()
    {
        optionsPanel.SetActive(!optionsPanel.activeSelf);
    }

    public void ClickMode()
    {
        GameSettings.useClick = true;
        optionsPanel.SetActive(false);
        Debug.Log("Modalità Click");
    }

    public void NoClickMode()
    {
        GameSettings.useClick = false;
        optionsPanel.SetActive(false);
        Debug.Log("Modalità NoClick");
    }
}