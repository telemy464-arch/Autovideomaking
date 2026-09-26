using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Net;
using System.Threading;
using System.Windows.Forms;

namespace MizanAIStudio
{
    class Program
    {
        static NotifyIcon trayIcon;
        static Process stProcess;

        static bool HasWriteAccess(string dir)
        {
            try
            {
                string testFile = Path.Combine(dir, ".write_test_" + Guid.NewGuid().ToString("N"));
                File.WriteAllText(testFile, "test");
                File.Delete(testFile);
                return true;
            }
            catch
            {
                return false;
            }
        }

        [STAThread]
        static void Main()
        {
            string rootDir = AppDomain.CurrentDomain.BaseDirectory;
            Directory.SetCurrentDirectory(rootDir);

            // 1. Automatic Elevation Check:
            // If the application is installed in a restricted directory (like Program Files)
            // and does not have write access, automatically re-launch with Administrator elevation!
            if (!HasWriteAccess(rootDir))
            {
                try
                {
                    ProcessStartInfo psiElevated = new ProcessStartInfo
                    {
                        FileName = Application.ExecutablePath,
                        UseShellExecute = true,
                        Verb = "runas"
                    };
                    Process.Start(psiElevated);
                    return;
                }
                catch
                {
                    MessageBox.Show(
                        "Mizan AI Video Studio needs write permissions to run.\nPlease click 'Yes' on the administrator prompt or install in your user directory.",
                        "Administrator Permission Required",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Warning
                    );
                    return;
                }
            }

            // 2. Prepend local bin to PATH for FFmpeg
            string binDir = Path.Combine(rootDir, "bin");
            string currentPath = Environment.GetEnvironmentVariable("PATH") ?? "";
            if (Directory.Exists(binDir) && !currentPath.Contains(binDir))
            {
                Environment.SetEnvironmentVariable("PATH", binDir + Path.PathSeparator + currentPath);
            }

            // 3. Ensure required directories and .env exist
            string envFile = Path.Combine(rootDir, ".env");
            string envExample = Path.Combine(rootDir, ".env.example");
            if (!File.Exists(envFile) && File.Exists(envExample))
            {
                File.Copy(envExample, envFile);
            }

            string outDir = Path.Combine(rootDir, "output");
            if (!Directory.Exists(outDir)) Directory.CreateDirectory(outDir);
            string tmpDir = Path.Combine(rootDir, "temp");
            if (!Directory.Exists(tmpDir)) Directory.CreateDirectory(tmpDir);

            // 4. Locate Python Executable (Bundled Portable Runtime first, then .venv, then fallback)
            string runtimePy = Path.Combine(rootDir, "runtime", "python.exe");
            string venvPy = Path.Combine(rootDir, ".venv", "Scripts", "python.exe");
            string chosenPy = null;

            if (File.Exists(runtimePy))
            {
                chosenPy = runtimePy;
            }
            else if (File.Exists(venvPy))
            {
                chosenPy = venvPy;
            }

            // 5. If neither exists, run self-healing auto-setup engine
            if (string.IsNullOrEmpty(chosenPy))
            {
                string psScript = Path.Combine(rootDir, "setup_and_run.ps1");
                if (File.Exists(psScript))
                {
                    ProcessStartInfo psiSetup = new ProcessStartInfo("powershell.exe", 
                        "-NoProfile -ExecutionPolicy Bypass -File \"" + psScript + "\"")
                    {
                        CreateNoWindow = false,
                        UseShellExecute = true
                    };
                    Process p = Process.Start(psiSetup);
                    p.WaitForExit();
                }

                if (File.Exists(runtimePy)) chosenPy = runtimePy;
                else if (File.Exists(venvPy)) chosenPy = venvPy;
            }

            // 6. Launch Streamlit Headless
            if (!string.IsNullOrEmpty(chosenPy) && File.Exists(chosenPy))
            {
                ProcessStartInfo psi = new ProcessStartInfo(chosenPy, "-m streamlit run app.py --server.headless true --theme.base dark")
                {
                    WorkingDirectory = rootDir,
                    CreateNoWindow = true,
                    UseShellExecute = false
                };
                psi.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";
                psi.EnvironmentVariables["PYTHONUTF8"] = "1";
                stProcess = Process.Start(psi);
            }

            // 7. Smart Browser Poller (Opens browser the exact moment server is ready)
            ThreadPool.QueueUserWorkItem((state) => {
                bool opened = false;
                for (int i = 0; i < 25; i++)
                {
                    Thread.Sleep(600);
                    try
                    {
                        HttpWebRequest req = (HttpWebRequest)WebRequest.Create("http://localhost:8501");
                        req.Timeout = 800;
                        using (HttpWebResponse resp = (HttpWebResponse)req.GetResponse())
                        {
                            if (resp.StatusCode == HttpStatusCode.OK)
                            {
                                Process.Start("http://localhost:8501");
                                opened = true;
                                break;
                            }
                        }
                    }
                    catch { }
                }
                if (!opened)
                {
                    try { Process.Start("http://localhost:8501"); } catch { }
                }
            });

            // 8. System Tray Manager
            Application.EnableVisualStyles();
            trayIcon = new NotifyIcon();
            trayIcon.Text = "Mizan AI Video Studio (Active)";
            
            string iconPath = Path.Combine(rootDir, "assets", "app_icon.ico");
            if (File.Exists(iconPath))
            {
                try { trayIcon.Icon = new Icon(iconPath); } catch { trayIcon.Icon = SystemIcons.Application; }
            }
            else
            {
                trayIcon.Icon = SystemIcons.Application;
            }
            
            trayIcon.Visible = true;

            ContextMenuStrip menu = new ContextMenuStrip();
            menu.Items.Add("🌐 Open Web Studio", null, (s, e) => {
                try { Process.Start("http://localhost:8501"); } catch { }
            });
            menu.Items.Add("📂 Open Output Videos", null, (s, e) => {
                Process.Start("explorer.exe", outDir);
            });
            menu.Items.Add("-");
            menu.Items.Add("❌ Exit Application", null, (s, e) => {
                trayIcon.Visible = false;
                if (stProcess != null && !stProcess.HasExited)
                {
                    try { stProcess.Kill(); } catch { }
                }
                Application.Exit();
            });

            trayIcon.ContextMenuStrip = menu;
            trayIcon.DoubleClick += (s, e) => {
                try { Process.Start("http://localhost:8501"); } catch { }
            };

            Application.Run();
        }
    }
}
