using System.Diagnostics;
using Microsoft.UI.Xaml;

namespace Zpace;

public sealed partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
    }

    private void ScanButton_Click(object sender, RoutedEventArgs e)
    {
        Debug.WriteLine("Scan clicked");
    }
}
