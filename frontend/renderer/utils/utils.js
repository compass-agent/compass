export const getNameFromPath = (path) => path.split(/[/\\]/).pop();

export const formatScriptForPlatform = (platform, script) => {
  if (platform === "win32") {
    return script.replace(/\\/g, "\\\\"); // Escape backslashes
  } else {
    // Adjust script for Linux/Mac (no escaping needed)
    return script.replace(/"/g, '\\"'); // Escape quotes if necessary
  }
};

export const parseTerminalCommand = (input) =>
  input
    .replace(/^powershell\.exe\s+-Command\s+"(.+)"$/, "$1") // Remove powershell.exe -Command and surrounding double quotes
    .replace(/^powershell\.exe\s+/, "") // Remove powershell.exe from the beginning of the command
    .replace(/'([^']+)'/g, "$1") // Remove unnecessary single quotes around paths
    .trim();


// Check if a character is a printable ASCII character
export const isPrintableASCII = (data) => {
  return data >= String.fromCharCode(32) && data <= String.fromCharCode(126);
};