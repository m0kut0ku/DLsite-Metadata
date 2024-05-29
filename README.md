# DLsite Metadata

This plugin is designed for the Calibre ebook management software and provides functionality to download metadata and cover images from DLsite.

## Features

- Retrieval of title, authors, summary, publisher, publication date, series, and tags
- Fetching high-resolution cover images
- Filtering by blacklisted words in the title or tags

## Installation

1. Open Calibre.
2. Go to "Preferences" > "Advanced" > "Plugins" > "Load Plugin from File".
3. Select the DLsite Metadata plugin ZIP file.
4. Ensure the plugin is enabled.

## Configuration

1. Navigate to Calibre's "Preferences" > "Sharing" > "Metadata Download".
2. Select "DLsite Metadata" and click "Configure Selected Source".
3. Adjust options as needed.

## Downloading Metadata

To retrieve metadata for multiple books at once, right-click the selected books, go to "Edit Metadata" > "Download Metadata and Covers". Only the first match is selected initially.

## Troubleshooting

- If the first match is incorrect, increase the "Number of matches to fetch" option and use the "Download metadata" button in the individual metadata editor to fetch metadata. This allows selection from possible matches.
- To output multiple results, a placeholder ISBN is output. Please remove this after fetching the data.
- If there are issues with series matching, confirm how the series is called on DLsite Store and adjust the title for matching.
- If the correct match is clear, enter the DLsite product ID in the form `dlsite:xxxxxxxxxxxxx` in the identifier field. The plugin performs metadata search using this product ID.
- Series volume cannot be retrieved; please input manually.

Using this plugin makes it easy to obtain metadata for books from DLsite.