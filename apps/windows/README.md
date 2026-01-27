# Zpace Windows App

A WinUI 3 desktop application for disk space analysis.

## Prerequisites

- Windows 10 version 1809 (build 17763) or later
- [Visual Studio 2026](https://visualstudio.microsoft.com/) with:
  - .NET 10 SDK
  - Windows App SDK workload
  - Windows 10 SDK (10.0.19041.0 or later)

## Build and Run

### Using Visual Studio

1. Open `Zpace.csproj` in Visual Studio 2022
2. Select your target platform (x64, x86, or ARM64)
3. Press F5 to build and run

### Using Command Line

```powershell
dotnet build -c Debug
dotnet run
```

## Project Structure

- `App.xaml` / `App.xaml.cs` - Application entry point
- `MainWindow.xaml` / `MainWindow.xaml.cs` - Main window with Scan button
- `Package.appxmanifest` - App package manifest
- `app.manifest` - Application manifest for Windows compatibility
