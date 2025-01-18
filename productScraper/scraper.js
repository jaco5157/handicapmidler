// Extract the desired strings from the page
const extractedStrings = Array.from(document.querySelectorAll(".product label"))
  .map(label => {
    // Split the text content by newlines and trim each line
    const lines = label.textContent.trim().split("\n").map(line => line.trim());

    // Find the line that starts with "Varenr."
    const varenrLine = lines.find(line => line.startsWith("Varenr."));

    // Extract and return the number after "Varenr." if the line exists
    return varenrLine ? varenrLine.split(" ")[1] : null;
  })
  .filter(Boolean); // Remove null values

// Convert the data to CSV format
const csvContent = extractedStrings.map(line => `"${line}"`).join("\n");

// Trigger a download of the CSV file
const blob = new Blob([csvContent], { type: "text/csv" });
const link = document.createElement("a");
link.href = URL.createObjectURL(blob);
link.download = "extracted_strings.csv";
document.body.appendChild(link);
link.click();
document.body.removeChild(link);