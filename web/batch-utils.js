/** Pure helpers shared by the batch interface and its regression tests. */
export function resultStatus(item) {
  if (item.status !== "done") return item.status;
  return item.result.is_blurry ? "blurry" : "clear";
}

export function sortResults(items, order) {
  return [...items].sort((a, b) => {
    if (order === "name") return a.file.name.localeCompare(b.file.name) || a.id - b.id;
    if (order === "score-asc" || order === "score-desc") {
      const left = a.result?.blur_score;
      const right = b.result?.blur_score;
      if (left == null) return right == null ? a.id - b.id : 1;
      if (right == null) return -1;
      return (order === "score-asc" ? left - right : right - left) || a.id - b.id;
    }
    return a.id - b.id;
  });
}

export function resultsCsv(items) {
  const columns = ["filename", "status", "blur_score", "threshold", "width", "height", "file_size", "message"];
  const cell = (value) => {
    let text = String(value ?? "");
    // Treat filenames and messages as text when opened by spreadsheet software.
    if (/^\s*[=+\-@]/u.test(text) || /^[\t\r\n]/u.test(text)) text = `'${text}`;
    return `"${text.replaceAll('"', '""')}"`;
  };
  const rows = items.map((item) => [
    item.file.name, resultStatus(item), item.result?.blur_score, item.result?.threshold,
    item.result?.width, item.result?.height, item.file.size, item.error || item.result?.message,
  ]);
  return [columns, ...rows].map((row) => row.map(cell).join(",")).join("\r\n") + "\r\n";
}
