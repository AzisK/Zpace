import SwiftUI

struct ContentView: View {
    @State private var outputText: String = ""
    @State private var isScanning: Bool = false

    var body: some View {
        VStack {
            Button(isScanning ? "Scanning..." : "Scan") {
                runScan()
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
            .disabled(isScanning)
            .padding(.top, 8)

            ScrollView {
                Text(outputText)
                    .font(.system(.body, design: .monospaced))
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .textSelection(.enabled)
            }
            .frame(maxHeight: .infinity)
            .background(Color(NSColor.textBackgroundColor))
            .cornerRadius(8)
        }
        .frame(width: 600, height: 500)
        .padding()
    }

    private func runScan() {
        isScanning = true
        outputText = ""

        Task {
            let output = await runZpaceCLI()
            await MainActor.run {
                outputText = output
                isScanning = false
            }
        }
    }

    private func runZpaceCLI() async -> String {
        let process = Process()
        let pipe = Pipe()

        process.executableURL = URL(fileURLWithPath: "/Users/azis/.local/bin/uv")
        process.arguments = ["run", "zpace"]
        process.currentDirectoryURL = findProjectRoot()
        process.standardOutput = pipe
        process.standardError = pipe

        do {
            try process.run()
            process.waitUntilExit()

            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            return String(data: data, encoding: .utf8) ?? "No output"
        } catch {
            return "Error running zpace: \(error.localizedDescription)"
        }
    }

    private func findProjectRoot() -> URL? {
        var url = URL(fileURLWithPath: #file)
        for _ in 0..<4 {
            url = url.deletingLastPathComponent()
        }
        return url
    }
}
