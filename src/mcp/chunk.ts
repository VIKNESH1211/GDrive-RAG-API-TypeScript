export function chunkText(
  fullText: string,
  maxChars: number = 500,
  overlap: number = 50
): string[] {
  const chunks: string[] = [];
  let start = 0;

  while (start < fullText.length) {
    const end = Math.min(start + maxChars, fullText.length);
    const chunk = fullText.slice(start, end).trim();

    if (chunk.length > 0) {
      chunks.push(chunk);
    }

    start += maxChars - overlap;
  }

  return chunks;
}