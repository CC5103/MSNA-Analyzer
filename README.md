# MSNA-Analyzer

**Read this in other languages: [English](README.md), [中文](README_zh.md), [日本語](README_jp.md).**

## Overview
MSNA-Analyzer is a tool designed for the analysis and visualization of muscle sympathetic nerve activity (MSNA), ECG, and blood pressure signals. With its PyQt5 interface, this software allows users to import, analyze, and visualize physiological data, supporting cardiovascular and neural signal studies. MSNA bursts can be detected both automatically and manually, offering users flexibility in their analysis. Recent updates include the option to use arrow keys instead of the mouse for faster burst identification, enhancing the efficiency of analysis.

## Sample Diagram
<div style="display: flex; justify-content: space-between;">
  <img src="image/Sample_diagram1.png" alt="Sample diagram 1" width="48%" />
  <img src="image/Sample_diagram2.png" alt="Sample diagram 2" width="48%" />
</div>

## Key Features
- **Automated Burst Detection**: Automatically detects MSNA bursts, reducing manual intervention.
- **Manual Identification**: Allows users to manually identify bursts, providing flexibility for precise analysis.
- **Arrow Key Control**: Use of arrow keys for burst identification accelerates the analysis process.
- **Output Formats**: Export results in `txt` or `Excel` formats for easy data access and further processing.
- **User-Friendly Interface**: Designed for a smooth and intuitive experience, with both automated and manual modes available.

## Installation

### Requirements
- Windows operating system
- .NET Framework 4.7.2 or higher

### How to Install
1. Download the latest version from the [Releases](https://github.com/CC5103/MSNA-Analyzer/releases) section.
2. Extract the `MSNAAnalyzer.exe` file from the zip archive.
3. Run the executable to launch the tool.

## Usage

### Automatic Mode
1. **Input**: Provide the input data file in `.txt` format.
2. **Action**: The tool will automatically detect and analyze MSNA bursts in the data.
3. **Output**: A results file will be generated in both `txt` and `Excel` formats.

### Manual Mode
1. **Input**: Provide the input data file in `.txt` format.
2. **Action**: Use the arrow keys to manually identify MSNA bursts or use the interface for precise control.
3. **Output**: A results file will be generated in both `txt` and `Excel` formats.

## Changelog

### v1.0.2
- Disabled the "Auto" button after pressing the "Start" button.

### v1.0.1
- UI Fix: Improved clarity by modifying the window title.
- Enhancement: Enhanced the default filename generation for Excel file saves.

### v1.0.0 (Initial Release)
- Introduced automatic burst detection.
- Implemented manual burst identification.
- Supported output in `txt` and `Excel` formats.

## Future Plans
- Add more algorithms for burst detection.
- Improve the user interface for better usability.
- Support additional data formats for import and export.

## License
This project is licensed under the GPL-3.0 License. See the [LICENSE](LICENSE) file for more details.

## Acknowledgments
Thanks to all contributors and testers for their valuable feedback.