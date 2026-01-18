# Zpace

[![PyPI version](https://img.shields.io/pypi/v/zpace?color=blue)](https://pypi.org/project/zpace/)
[![Tests](https://github.com/AzisK/Zpace/actions/workflows/ci.yml/badge.svg)](https://github.com/AzisK/Zpace/actions/workflows/ci.yml)

[Changelog](https://github.com/AzisK/Zpace/blob/main/CHANGELOG.md) · [Architecture](https://github.com/AzisK/Zpace/blob/main/ARCHITECTURE.md)

A CLI tool to discover what's hogging your disk space!

The tool shows the largest files in each category of files (videos, pictures, documents etc.) as well as the largest special directories as apps in MacOS, Python virtual environments, node_modules etc.

It's built to indentify the biggest chunks of data that could potentially free up the space for something else.

## Features

- 📊 Smart Categorization - Groups files by type (Documents, Videos, Code, Pictures, etc.)
- 📦 Special Directory Detection - Identifies space-hungry directories like MacOS apps, node_modules, Python virtual environments, and build artifacts
- 🎯 Actionable Insights - Shows deletable units to help you quickly free up space
- ⚡ Fast Scanning - Efficient traversal with real-time progress tracking
- 🔍 Sparse File Handling - Correctly reports actual disk usage for Docker images and other sparse files
- 🎨 Clean Output - Organized and clear display with helpful statistics

## Installation

### macOS / Linux (Homebrew)

```bash
brew tap AzisK/zpace
brew install zpace
```

### Windows (Scoop)

```powershell
scoop bucket add zpace https://github.com/AzisK/scoop-zpace
scoop install zpace
```

### Using uv

```bash
uv tool install zpace
```

### Using pipx

```bash
pipx install zpace
```

### Using pip

```bash
pip install zpace
```

## Usage

### Basic Commands
```bash
# Scan your home directory (default)
zpace

# Scan a specific directory
zpace /path/to/directory

# Scan current directory
zpace .
```

### Options
```bash
# Show top 20 items per category (default: 10)
zpace -n 20

# Set minimum file size to 1MB (default: 100KB)
zpace -m 1024

# Combine options
zpace ~/Documents -n 15 -m 500
```

### Example Output

<details>
<summary>Open example output</summary>

```bash
zpace

DISK USAGE
======================================================================================================================
  Free:  533.01 GB / 926.35 GB
  Used:  393.34 GB (42.5%)
  Trash: 310.41 MB
======================================================================================================================

SCANNING: /Users/azis
   Min size: 100 KB

Scanning:  53%|████████████████████████████████████                                | 224G/422G [00:55<00:49, 4.05GB/s]

SCAN COMPLETE!
   Found 593,044 files
   Found 420 special directories
   Total size: 208.58 GB

======================================================================================================================
SPECIAL DIRECTORIES
======================================================================================================================

----------------------------------------------------------------------------------------------------------------------
Build Artifacts (10 directories)
----------------------------------------------------------------------------------------------------------------------
       4.50 GB  /Users/azis/Documents/Github/ladybird/Build
      30.63 MB  /Users/azis/Documents/Github/trino/plugin/trino-tpch/target
      22.89 MB  /Users/azis/Documents/Github/trino/core/trino-web-ui/target
      12.11 MB  /Users/azis/.antigravity/extensions/ms-python.python-2025.16.0-universal/out
       8.52 MB  /Users/azis/Documents/Github/trino/core/trino-spi/target
       7.65 MB  /Users/azis/Library/Caches/com.apple.python/Users/azis/Documents/Github/ladybird/Build
       6.94 MB  /Users/azis/Downloads/FromLegacyLaptop/Books/PythonApp/build
       6.29 MB  /Users/azis/Documents/Github/trino/core/trino-grammar/target
       5.46 MB  /Users/azis/.antigravity/extensions/ms-python.debugpy-2025.14.1-darwin-arm64/dist
       5.15 MB  /Users/azis/Documents/Github/trino/core/trino-parser/target

----------------------------------------------------------------------------------------------------------------------
Bun Modules (1 directories)
----------------------------------------------------------------------------------------------------------------------
       1.14 GB  /Users/azis/.bun

----------------------------------------------------------------------------------------------------------------------
Git Repos (10 directories)
----------------------------------------------------------------------------------------------------------------------
     312.73 MB  /Users/azis/Documents/Github/ladybird/.git
     308.82 MB  /Users/azis/Documents/Github/trino/.git
     184.30 MB  /Users/azis/Documents/Github/lightdash/.git
      28.68 MB  /Users/azis/Documents/Github/myblog/.git
      14.29 MB  /Users/azis/Documents/Github/OpenCut/.git
      11.76 MB  /Users/azis/Documents/Github/valuecell/.git
       6.03 MB  /Users/azis/.oh-my-zsh/.git
       3.49 MB  /Users/azis/Downloads/FromLegacyLaptop/Books/wcc-data-2019/.git
       2.04 MB  /Users/azis/Documents/Github/Zpace/.git
       1.94 MB  /Users/azis/Downloads/FromLegacyLaptop/Books/we-can-code-maps/.git

----------------------------------------------------------------------------------------------------------------------
IDE Config (2 directories)
----------------------------------------------------------------------------------------------------------------------
     714.48 MB  /Users/azis/.vscode
     792.00 KB  /Users/azis/Library/Caches/com.apple.python/Users/azis/.vscode

----------------------------------------------------------------------------------------------------------------------
Node Modules (10 directories)
----------------------------------------------------------------------------------------------------------------------
       1.12 GB  /Users/azis/Documents/Github/OpenCut/node_modules
     608.26 MB  /Users/azis/Documents/Github/trino/core/trino-web-ui/src/main/resources/webapp-preview/node_modules
     409.03 MB  /Users/azis/Library/Application Support/Zed/external_agents/gemini/0.16.0/node_modules
     395.82 MB  /Users/azis/Documents/Github/trino/core/trino-web-ui/src/main/resources/webapp/src/node_modules
     255.84 MB  /Users/azis/Downloads/FromLegacyLaptop/Books/UI-Academy/homework/node_modules
     248.01 MB  /Users/azis/Downloads/FromLegacyLaptop/Books/UI-Academy/autocomplete-api-app/node_modules
     206.77 MB  /Users/azis/Library/Application Support/Zed/external_agents/claude-code-acp/0.10.6/node_modules
      17.30 MB  /Users/azis/Documents/Github/trino/.node/node/node_modules
      15.80 MB  /Users/azis/Library/Application Support/discord/0.0.364/modules/discord_spellcheck/node_modules
      14.09 MB  /Users/azis/Library/Application Support/JetBrains/PyCharm2025.2/plugins/javascript-plugin/jsLanguageServicesImpl/typescript/node_modules

----------------------------------------------------------------------------------------------------------------------
Package Caches (10 directories)
----------------------------------------------------------------------------------------------------------------------
     575.89 MB  /Users/azis/.m2
     502.41 MB  /Users/azis/.cache
     237.80 MB  /Users/azis/.npm
       3.61 MB  /Users/azis/.local/share/uv/tools/marimo/lib/python3.14/site-packages/pygments/lexers/__pycache__
       3.45 MB  /Users/azis/.local/share/uv/python/cpython-3.13.5-macos-aarch64-none/lib/python3.13/__pycache__
       3.21 MB  /Users/azis/.local/share/uv/python/cpython-3.14.0-macos-aarch64-none/lib/python3.14/__pycache__
       3.10 MB  /Users/azis/.local/share/uv/python/pypy-3.11.13-macos-aarch64-none/lib/pypy3.11/__pycache__
       2.59 MB  /Users/azis/.local/share/uv/python/cpython-3.11.13-macos-aarch64-none/lib/python3.11/__pycache__
       2.21 MB  /Users/azis/.local/share/uv/python/cpython-3.12.11-macos-aarch64-none/lib/python3.12/__pycache__
       1.82 MB  /Users/azis/.local/share/uv/python/cpython-3.10.18-macos-aarch64-none/lib/python3.10/__pycache__

----------------------------------------------------------------------------------------------------------------------
Virtual Environments (10 directories)
----------------------------------------------------------------------------------------------------------------------
     580.26 MB  /Users/azis/Downloads/FromLegacyLaptop/testing-python-data-science-code-2477020/.venv
     401.46 MB  /Users/azis/Downloads/FromLegacyLaptop/FastApi/.venv
     282.45 MB  /Users/azis/Downloads/FromLegacyLaptop/Books/snowflake/.venv
     107.12 MB  /Users/azis/Documents/Github/Zpace/.venv
      95.05 MB  /Users/azis/Documents/Github/DbtPlay/.venv
      69.30 MB  /Users/azis/Downloads/FromLegacyLaptop/Puddle/.venv
      28.21 MB  /Users/azis/.Trash/.venv
      22.79 MB  /Users/azis/Downloads/FromLegacyLaptop/Books/squalo/.venv
      22.79 MB  /Users/azis/Downloads/FromLegacyLaptop/Books/squalo_old/.venv
      20.97 MB  /Users/azis/Downloads/FromLegacyLaptop/Photos/Flask/.venv

----------------------------------------------------------------------------------------------------------------------
macOS Apps (10 directories)
----------------------------------------------------------------------------------------------------------------------
     918.15 MB  /Users/azis/Library/Application Support/Microsoft/EdgeUpdater/apps/msedge-stable/142.0.3595.53/Microsoft Edge.app
     915.88 MB  /Users/azis/Library/Application Support/Microsoft/EdgeUpdater/apps/msedge-stable/141.0.3537.99/Microsoft Edge.app
     410.54 MB  /Users/azis/Library/Caches/com.microsoft.VSCode.ShipIt/update.17AFGQ1/Visual Studio Code.app
      30.33 MB  /Users/azis/Library/Caches/JetBrains/PyCharm2025.2/full-line/models/baa3b306-cd6c-3e90-9dc3-a8d38bd594ed/full-line-inference.zip_extracted/full-line-inference.app
      29.61 MB  /Users/azis/Library/Application Support/uTorrent Web/helper.app
      28.75 MB  /Users/azis/Library/Caches/JetBrains/PyCharm2025.2/semantic-search/server/3.0.169/embeddings-server.app
      22.56 MB  /Users/azis/Library/Application Support/Google/GoogleUpdater/143.0.7482.0/GoogleUpdater.app
      16.79 MB  /Users/azis/Library/Application Support/Microsoft/EdgeUpdater/137.0.3249.0/EdgeUpdater.app
      16.79 MB  /Users/azis/Library/Application Support/Microsoft/EdgeUpdater/apps/msedge-updater/137.0.3249.0/EdgeUpdater.app
      13.09 MB  /Users/azis/Library/Application Support/Dropbox/DropboxUpdater/123.0.6299.129/DropboxUpdater.app

======================================================================================================================
LARGEST FILES BY CATEGORY
======================================================================================================================

----------------------------------------------------------------------------------------------------------------------
Archives (10 files)
----------------------------------------------------------------------------------------------------------------------
       1.08 GB  /Users/azis/Downloads/FromLegacyLaptop/wetransfer_2022-01-22_misko_motes_nuotr-1-jpg_2022-01-24_0704.zip
     424.90 MB  /Users/azis/Library/Caches/Homebrew/downloads/fcccf85c4a2c3a5879c5d42434f627e765a7349e491a299516fd6012cac4122a--llvm--21.1.5.arm64_tahoe.bottle.tar.gz
     334.29 MB  /Users/azis/Library/Caches/Homebrew/downloads/711cf583f7090481831de4ff56fd47911c4c4a6f836ce1a3dda28d74bcc49f28--llvm@20--20.1.8.arm64_tahoe.bottle.tar.gz
     225.71 MB  /Users/azis/Library/Caches/com.nordvpn.macos/org.sparkle-project.Sparkle/PersistentDownloads/TImW5osHW/NordVPN 343/NordVPN.zip
     207.71 MB  /Users/azis/Library/Caches/Homebrew/downloads/4cbe879eb7a57f7562fb6d1246e33fc5879aeff70f67d0e7168498e4cc2aa10b--openjdk--25.arm64_tahoe.bottle.tar.gz
     186.07 MB  /Users/azis/Library/Caches/JetBrains/PyCharm2025.2/plugins/fullLine.zip
     162.95 MB  /Users/azis/Downloads/FromLegacyLaptop/wetransfer_img_20210725_213726-jpg_2021-09-22_1459.zip
     134.37 MB  /Users/azis/Downloads/FromLegacyLaptop/Ąžuolas_Krušna_1993_02_11_NNTViewer&DICOM.zip
     121.73 MB  /Users/azis/Library/Caches/Homebrew/downloads/e2c6e06e84cc40dac4e77966009d8fa5829ad2b482c551fe291c1050ca8cad35--qtwebengine--6.9.3.arm64_tahoe.bottle.tar.gz
     107.12 MB  /Users/azis/Library/Application Support/Caches/notion-updater/pending/Notion-arm64-4.22.0.zip

----------------------------------------------------------------------------------------------------------------------
Code (10 files)
----------------------------------------------------------------------------------------------------------------------
      12.30 MB  /Users/azis/.rustup/toolchains/stable-aarch64-apple-darwin/share/doc/rust/COPYRIGHT.html
       8.63 MB  /Users/azis/Library/Application Support/JetBrains/PyCharm2025.2/plugins/javascript-plugin/jsLanguageServicesImpl/external/typescript.js
       8.28 MB  /Users/azis/.rustup/toolchains/stable-aarch64-apple-darwin/share/doc/rust/html/src/core/stdarch/crates/core_arch/src/arm_shared/neon/generated.rs.html
       8.03 MB  /Users/azis/Library/Application Support/JetBrains/PyCharm2025.2/plugins/jupyter-plugin/jupyter-web/main.js
       7.33 MB  /Users/azis/.rustup/toolchains/stable-aarch64-apple-darwin/share/doc/rust/html/src/core/stdarch/crates/core_arch/src/x86/avx512f.rs.html
       7.13 MB  /Users/azis/Library/Application Support/JetBrains/PyCharm2025.2/plugins/vuejs/vue-language-server/bin/vue-language-server.js
       5.20 MB  /Users/azis/go/pkg/mod/golang.org/x/text@v0.27.0/date/tables.go
       5.00 MB  /Users/azis/.rustup/toolchains/stable-aarch64-apple-darwin/share/doc/rust/html/rustc/searchindex-237cff1f.js
       5.00 MB  /Users/azis/.local/share/uv/tools/marimo/lib/python3.14/site-packages/marimo/_static/assets/react-plotly-Cb9HWGJX.js
       4.72 MB  /Users/azis/go/pkg/mod/golang.org/x/text@v0.0.0-20170915032832-14c0d48ead0c/collate/tables.go

----------------------------------------------------------------------------------------------------------------------
Disk Images (10 files)
----------------------------------------------------------------------------------------------------------------------
       4.91 GB  /Users/azis/Documents/26100.4349.250607-1500.ge_release_svc_refresh_CLIENTCONSUMER_RET_A64FRE_en-us.iso
     124.56 MB  /Users/azis/Library/Caches/Homebrew/downloads/9e8661acbb5a3c3a251f937b59a4af25ec69d224bc50a0a1b99b0502e2fc092b--dbeaver-ce-25.1.5-macos-aarch64.dmg
     121.20 MB  /Users/azis/Library/Containers/com.utmapp.UTM/Data/Library/Application Support/GuestSupportTools/utm-guest-tools-latest.iso
     110.10 MB  /Users/azis/Library/Caches/Homebrew/downloads/be14ce50da21683d9f7514acd678a97306f1a3555ca57ef5b7468f1de82e58d8--marktext-arm64.dmg
      45.68 MB  /Users/azis/Downloads/Ollama.dmg
     352.00 KB  /Users/azis/Library/Metadata/CoreSpotlight/Priority/index.spotlightV3/Cache/41723070/4172307026dcb432.img
     352.00 KB  /Users/azis/Library/Metadata/CoreSpotlight/Priority/index.spotlightV3/Cache/41723070/41723070310f136c.img
     352.00 KB  /Users/azis/Library/Metadata/CoreSpotlight/Priority/index.spotlightV3/Cache/41723070/4172307066647ee3.img
     352.00 KB  /Users/azis/Library/Metadata/CoreSpotlight/Priority/index.spotlightV3/Cache/41723070/417230705b8c43ab.img
     352.00 KB  /Users/azis/Library/Metadata/CoreSpotlight/Priority/index.spotlightV3/Cache/41723070/41723070bcf40abf.img

----------------------------------------------------------------------------------------------------------------------
Documents (10 files)
----------------------------------------------------------------------------------------------------------------------
     528.17 MB  /Users/azis/Downloads/FromLegacyLaptop/2022_RM Dalyvio atmintinė .pdf
     106.37 MB  /Users/azis/Downloads/FromLegacyLaptop/Lernziel Deutsch Grundstufe 1_Lehrbuch.pdf
      87.84 MB  /Users/azis/Documents/Knygės/Techninės/Gayle Laakmann McDowell-Cracking the Coding Interview, 6th Edition_ 189 Programming Questions and Solutions-CareerCup (2015).pdf
      84.88 MB  /Users/azis/Downloads/Knygės/OnceARunner.pdf
      73.59 MB  /Users/azis/Downloads/Knygės/Leonard Susskind. The Black Hole War.pdf
      65.47 MB  /Users/azis/Documents/Maciunas, George_ Schmidt-Burkhardt, Astrit - Maciunas Learning Machines _ from art history to a chronology of Fluxus (2003, Fluxus Collection, Vice Versa, Berlin) - libgen.lc.pdf
      58.75 MB  /Users/azis/Downloads/FromLegacyLaptop/Pysanka Coursebook.pdf
      55.41 MB  /Users/azis/Downloads/Ukraina/History of Ukraine.pdf
      38.19 MB  /Users/azis/Documents/Knygės/Techninės/Distributed systems.pdf
      37.88 MB  /Users/azis/Downloads/Račkauskas-Graikų-kalbos-gramatika-d.1-1930.pdf

----------------------------------------------------------------------------------------------------------------------
JSON/YAML (10 files)
----------------------------------------------------------------------------------------------------------------------
      32.84 MB  /Users/azis/Downloads/FromLegacyLaptop/Books/hackathon18/bus_stop_times.json
      30.25 MB  /Users/azis/Library/Caches/Homebrew/api/formula.jws.json
      20.24 MB  /Users/azis/Library/Group Containers/3KKZV48AQD.com.betafish.adblock-mac/sharedFilterlist+exceptionrules.json
      17.52 MB  /Users/azis/Library/Application Support/Dia/BlockList.json
      16.50 MB  /Users/azis/Library/Group Containers/3KKZV48AQD.com.betafish.adblock-mac/sharedFilterlist+exceptionrules_original.json
      15.30 MB  /Users/azis/Library/Group Containers/3KKZV48AQD.com.betafish.adblock-mac/sharedFilterlist.json
      14.27 MB  /Users/azis/Library/Caches/Homebrew/api/cask.jws.json
      12.89 MB  /Users/azis/Library/Caches/JetBrains/PyCharm2025.2/python_packages/pypi-cache.json
      12.25 MB  /Users/azis/Library/Group Containers/3KKZV48AQD.com.betafish.adblock-mac/sharedFilterlist_original.json
      11.24 MB  /Users/azis/Downloads/FromLegacyLaptop/Books/hackathon18/bus_routes_coordinates.json

----------------------------------------------------------------------------------------------------------------------
Music (10 files)
----------------------------------------------------------------------------------------------------------------------
      34.32 MB  /Users/azis/Downloads/FromLegacyLaptop/Photos/Analysis-20180831-TheTruthAboutBritainsBeggars.mp3
      34.10 MB  /Users/azis/Downloads/FromLegacyLaptop/Photos/Analysis-20190108-TheTrumpedRepublicans.mp3
      27.47 MB  /Users/azis/Documents/Knygės/Literatūra/Donbaso-dziazas/01 Pradzia.mp3
      26.43 MB  /Users/azis/Downloads/FromLegacyLaptop/Photos/Analysis-20181001-PowerShift.mp3
      26.35 MB  /Users/azis/Downloads/FromLegacyLaptop/Photos/Analysis-20181022-ThePupilPremium.mp3
      26.35 MB  /Users/azis/Downloads/FromLegacyLaptop/Photos/Analysis-20181008-OperationToryBlackVote.mp3
      26.21 MB  /Users/azis/Downloads/FromLegacyLaptop/Photos/Analysis-20181029-DoAssassinationsWork.mp3
      26.07 MB  /Users/azis/Downloads/FromLegacyLaptop/Photos/Analysis-20181015-NorthernIrelandWhereNext.mp3
      26.05 MB  /Users/azis/Downloads/FromLegacyLaptop/Photos/Analysis-20181105-HowToKillADemocracy.mp3
      26.04 MB  /Users/azis/Downloads/FromLegacyLaptop/Photos/Analysis-20190114-AmericasFriends.mp3

----------------------------------------------------------------------------------------------------------------------
Others (10 files)
----------------------------------------------------------------------------------------------------------------------
      45.88 GB  /Users/azis/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw
       9.66 GB  /Users/azis/Library/Containers/com.utmapp.UTM/Data/Documents/Windows.utm/Data/9509DAE3-A9A0-40A0-908F-D127AD9C255E.qcow2
       4.77 GB  /Users/azis/Library/Caches/llama.cpp/unsloth_DeepSeek-R1-0528-Qwen3-8B-GGUF_DeepSeek-R1-0528-Qwen3-8B-UD-Q4_K_XL.gguf
       1.02 GB  /Users/azis/Library/Containers/llc.turing.CrystalFetch/Data/tmp/CFNetworkDownload_OwasdY.tmp
    1016.46 MB  /Users/azis/Library/Containers/llc.turing.CrystalFetch/Data/tmp/CFNetworkDownload_roxzKq.tmp
     635.91 MB  /Users/azis/Library/Application Support/Google/GoogleUpdater/crx_cache/142138d1a14e882b8ecd9a124261d6b65856ff4b78699fe88a36fbd0bfcb1d7d
     627.64 MB  /Users/azis/Library/Application Support/Arc/User Data/Default/WebStorage/171/CacheStorage/a3290f0b-8f2b-40ef-889b-a6375651f64f/528d4310e3ee4d43_0
     475.02 MB  /Users/azis/Library/Containers/llc.turing.CrystalFetch/Data/tmp/CFNetworkDownload_b7ndIa.tmp
     436.64 MB  /Users/azis/Pictures/Photos Library.photoslibrary/database/Photos.sqlite
     395.43 MB  /Users/azis/Library/Application Support/Microsoft/EdgeUpdater/crx_cache/713A19BE1D3C660E1F29814DE9E5877ADCB4839F25B9C781AF3028E3B2148BC4

----------------------------------------------------------------------------------------------------------------------
Pictures (10 files)
----------------------------------------------------------------------------------------------------------------------
      20.58 MB  /Users/azis/Downloads/FromLegacyLaptop/IMG_20210731_170131.jpg
      18.60 MB  /Users/azis/Library/Containers/com.apple.wallpaper.agent/Data/Library/Caches/com.apple.wallpaper.caches/extension-com.apple.wallpaper.extension.aerials/d867d11eadaf28227543ca437ef2e7109c19db1d77a24a17d7715d869653a7db-2940-1912-0-41c73805d2800000.bmp
      18.60 MB  /Users/azis/Library/Containers/com.apple.wallpaper.agent/Data/Library/Caches/com.apple.wallpaper.caches/extension-com.apple.wallpaper.extension.aerials/0649a787fa411f1e60409bffd73ed20a8bd4e40b431f96fad1f0520f97fc08d0-2940-1912-0-41c744056d7551f6.bmp
      18.60 MB  /Users/azis/Library/Containers/com.apple.wallpaper.agent/Data/Library/Caches/com.apple.wallpaper.caches/extension-com.apple.wallpaper.extension.aerials/53f5af35645abdda789120796703282cb72fa976e3f3571f4200355c18206169-2940-1912-0-41c740a3950a40e0.bmp
      15.64 MB  /Users/azis/Downloads/FromLegacyLaptop/Photos/20201024_123525.jpg
      14.65 MB  /Users/azis/Downloads/Nuotraukos/Nikon/_DSC1737.JPG
      14.45 MB  /Users/azis/Downloads/Nuotraukos/Nikon/_DSC1747.JPG
      14.34 MB  /Users/azis/Downloads/Nuotraukos/Nikon/_DSC1746.JPG
      14.34 MB  /Users/azis/Downloads/Nuotraukos/Nikon/_DSC2931.JPG
      14.22 MB  /Users/azis/Downloads/Nuotraukos/Nikon/_DSC1744.JPG

----------------------------------------------------------------------------------------------------------------------
Videos (10 files)
----------------------------------------------------------------------------------------------------------------------
     986.90 MB  /Users/azis/Downloads/Friendly Python Classes Screen Recording 2024-11-30 at 11.30.15 AM.mov
     519.87 MB  /Users/azis/Downloads/Filmai/Uga/Uga.mp4
     453.21 MB  /Users/azis/Library/Application Support/com.apple.wallpaper/aerials/videos/6D6834A4-2F0F-479A-B053-7D4DC5CB8EB7.mov
     445.41 MB  /Users/azis/Library/Application Support/com.apple.wallpaper/aerials/videos/4C108785-A7BA-422E-9C79-B0129F1D5550.mov
     224.91 MB  /Users/azis/Downloads/FromLegacyLaptop/Photos/Wellbeing Series - Prioritization - Recording.mp4
     167.31 MB  /Users/azis/Downloads/IMG_4889.MOV
     167.21 MB  /Users/azis/Downloads/IMG_4792.MOV
     163.02 MB  /Users/azis/Documents/IMG_4147.MOV
     157.58 MB  /Users/azis/Downloads/IMG_4891.MOV
     156.83 MB  /Users/azis/Downloads/Bouldering/IMG_4145.MOV
======================================================================================================================
```
</details>

### Tips

```bash
# Find all node_modules directories
zpace ~ -n 50 | grep "node_modules"

# Check what's in a specific directory
zpace ~/.cache

# Find largest files system-wide (requires sudo)
sudo zpace / -n 20
```

### macOS Permissions
If you see "Access Denied" for the Trash bin or other directories, you need to grant **Full Disk Access** to your terminal application (e.g., Terminal, iTerm2, VS Code).

1. Open **System Settings** -> **Privacy & Security** -> **Full Disk Access**.
2. Click the `+` button and add your terminal application.
3. Restart your terminal.

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/azisk/zpace.git
cd zpace

# Install dependencies
uv sync

# Run locally
uv run zpace
```

### Code Quality

The project uses Ruff for linting, formatting, and import sorting:

```bash
# Format code
uv run ruff format

# Lint code
uv run ruff check

# Fix auto-fixable issues
uv run ruff check --fix

# Run all pre-commit checks manually
uv run pre-commit run --all-files
```

### Testing

```bash
# Run all tests
uv run pytest -v

# Run unit tests only
uv run pytest test_unit.py -v

# Run integration tests only
uv run pytest test_integration.py -v

# Test across multiple Python versions (optional)
./testVersions.sh
```

### Project Structure
```
zpace/
├── zpace/
│   ├── __init__.py
│   ├── main.py
│   ├── core.py
│   ├── config.py
│   └── utils.py
├── main.py           # Entry point
├── pyproject.toml    # Project configuration
├── README.md         # This file
└── CHANGELOG.md      # Version history
```

### Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

### License
Apache 2.0 License - see [LICENSE](https://github.com/AzisK/Zpace/blob/main/LICENSE.txt) for details.

### Support

- 🐛 [Report a bug](https://github.com/AzisK/Zpace/issues)
- 💡 [Request a feature](https://github.com/AzisK/Zpace/issues)
- ⭐ Star the repo if you find it useful!

---

Made with love for people tired of full disks
