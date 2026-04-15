using UnityEngine;

public class OptionsMenu : MonoBehaviour
{
    public GameObject optionsPanel;

    public void OpenOptions()
    {
        optionsPanel.SetActive(true);
    }

    public void SelectPrato()
    {
        GameSettings.selectedBackground = "Prato";
    }

    public void SelectDeserto()
    {
        GameSettings.selectedBackground = "Deserto";
    }
}