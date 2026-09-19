using UnityEngine;

public class FullscreenManager : MonoBehaviour
{
    void Start()
    {
        Screen.SetResolution(Screen.currentResolution.width, Screen.currentResolution.height, true);
    }
}