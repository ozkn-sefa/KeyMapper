// klvye123_dll.cpp
#include <windows.h>
#include <string>
#include <vector>
#include <sstream>
#include <atomic>
#include <algorithm>
#include <functional>

typedef void(__stdcall* KeyCallback)(const char*);

static KeyCallback g_callback = nullptr;
static std::atomic<bool> g_running(false);
static HANDLE g_thread = nullptr;
static HWND g_hwnd = nullptr;

// =====================================================
//  Cihaz için sabit kimlik üretimi
//  - HID klavye: vid_xxxx&pid_yyyy
//  - Diğerleri: ACPI_DEVICE_XXXX (hash)
// =====================================================
static std::string GetDeviceUniqueId(HANDLE hDevice)
{
    std::string devicePath;

    if (hDevice)
    {
        UINT size = 0;
        // Önce gerekli boyutu al
        if (GetRawInputDeviceInfoA(hDevice, RIDI_DEVICENAME, NULL, &size) > 0 && size > 1)
        {
            std::vector<char> buf(size + 1);
            if (GetRawInputDeviceInfoA(hDevice, RIDI_DEVICENAME, buf.data(), &size) > 0)
            {
                devicePath = std::string(buf.data());
            }
        }
    }

    // Eğer path hiç alınamadıysa bile sabit bir fallback üret
    if (devicePath.empty())
    {
        std::hash<std::string> hasher;
        size_t h = hasher(std::string("UNKNOWN_DEVICE"));
        std::ostringstream oss;
        oss << "ACPI_DEVICE_" << std::hex << std::uppercase << (h & 0xFFFF);
        return oss.str();
    }

    // Lowercase kopya
    std::string lower = devicePath;
    std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);

    // Eğer HID yolunda VID/PID varsa → doğrudan onu kullan
    size_t vid_pos = lower.find("vid_");
    size_t pid_pos = lower.find("pid_");
    if (vid_pos != std::string::npos && pid_pos != std::string::npos)
    {
        std::string vid_str = lower.substr(vid_pos, 8); // "vid_1234"
        std::string pid_str = lower.substr(pid_pos, 8); // "pid_5678"
        return vid_str + "&" + pid_str;
    }

    // ACPI / özel cihaz → path üzerinden sabit hash
    std::hash<std::string> hasher;
    size_t h = hasher(lower);
    std::ostringstream oss;
    oss << "ACPI_DEVICE_" << std::hex << std::uppercase << (h & 0xFFFF);
    return oss.str();
}

// =====================================================
//  JSON
// =====================================================
static std::string MakeJson(const std::string& dev, unsigned int vkey)
{
    std::ostringstream oss;
    oss << "{ \"device\":\"" << dev << "\", \"vkey\":" << vkey << " }";
    return oss.str();
}

// =====================================================
//  Window Proc — sadece keydown gönder
// =====================================================
LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam)
{
    if (msg == WM_INPUT)
    {
        UINT size = 0;
        GetRawInputData((HRAWINPUT)lParam, RID_INPUT, NULL, &size, sizeof(RAWINPUTHEADER));
        if (size == 0) return 0;

        std::vector<BYTE> data(size);
        if (GetRawInputData((HRAWINPUT)lParam, RID_INPUT, data.data(), &size, sizeof(RAWINPUTHEADER)) == (UINT)-1)
            return 0;

        RAWINPUT* raw = (RAWINPUT*)data.data();
        if (!raw) return 0;

        if (raw->header.dwType == RIM_TYPEKEYBOARD)
        {
            // Sadece keydown (RI_KEY_BREAK yoksa)
            if (!(raw->data.keyboard.Flags & RI_KEY_BREAK))
            {
                HANDLE dev = raw->header.hDevice;
                unsigned int vkey = raw->data.keyboard.VKey;
                std::string id = GetDeviceUniqueId(dev);

                if (g_callback)
                {
                    std::string json = MakeJson(id, vkey);
                    g_callback(json.c_str());
                }
            }
        }
    }

    return DefWindowProcW(hwnd, msg, wParam, lParam);
}

// =====================================================
//  Listener Thread
// =====================================================
static DWORD WINAPI ListenerThread(LPVOID)
{
    const wchar_t CLASS_NAME[] = L"KLVYE123_RAWINPUT";

    WNDCLASSW wc = {};
    wc.lpfnWndProc = WndProc;
    wc.lpszClassName = CLASS_NAME;
    RegisterClassW(&wc);

    g_hwnd = CreateWindowExW(
        0, CLASS_NAME, L"HiddenRawInputWindow",
        0, 0, 0, 0, 0,
        HWND_MESSAGE, NULL, NULL, NULL);

    RAWINPUTDEVICE rid;
    rid.usUsagePage = 0x01;  // Generic desktop controls
    rid.usUsage = 0x06;      // Keyboard
    rid.dwFlags = RIDEV_INPUTSINK;
    rid.hwndTarget = g_hwnd;
    RegisterRawInputDevices(&rid, 1, sizeof(rid));

    MSG msg;
    while (g_running && GetMessageW(&msg, NULL, 0, 0) > 0)
    {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }

    g_hwnd = NULL;
    g_running = false;
    return 0;
}

// =====================================================
//  DLL Exportları
// =====================================================
extern "C" __declspec(dllexport)
void __stdcall Initialize(KeyCallback cb)
{
    g_callback = cb;
}

extern "C" __declspec(dllexport)
BOOL __stdcall StartListener()
{
    if (g_running) return TRUE;
    g_running = true;
    g_thread = CreateThread(NULL, 0, ListenerThread, NULL, 0, NULL);
    return g_thread != NULL;
}

extern "C" __declspec(dllexport)
void __stdcall StopListener()
{
    if (!g_running) return;

    g_running = false;

    if (g_hwnd)
        PostMessageW(g_hwnd, WM_CLOSE, 0, 0);

    if (g_thread)
    {
        WaitForSingleObject(g_thread, 2000);
        CloseHandle(g_thread);
        g_thread = NULL;
    }
}

BOOL APIENTRY DllMain(HMODULE, DWORD reason, LPVOID)
{
    if (reason == DLL_PROCESS_DETACH)
        StopListener();
    return TRUE;
}
