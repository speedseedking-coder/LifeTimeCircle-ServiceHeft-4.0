function normalizeBlocks(content: string): string[] {
  return content
    .replace(/\r\n?/g, "\n")
    .trim()
    .split(/\n{2,}/)
    .map((block) => block.trim())
    .filter(Boolean);
}

export default function EditorialRichText(props: { content: string }): JSX.Element {
  const blocks = normalizeBlocks(props.content);

  return (
    <section className="ltc-article__content">
      {blocks.map((block, index) => {
        const lines = block.split("\n").map((line) => line.trim()).filter(Boolean);
        if (lines.length === 1 && /^\*\*.+\*\*$/.test(lines[0])) {
          return (
            <strong key={index} className="ltc-article__heading">
              {lines[0].replace(/^\*\*/, "").replace(/\*\*$/, "")}
            </strong>
          );
        }

        if (lines.length > 0 && lines.every((line) => line.startsWith("- "))) {
          return (
            <ul key={index} className="ltc-article__list">
              {lines.map((line, itemIndex) => (
                <li key={itemIndex}>{line.replace(/^- /, "")}</li>
              ))}
            </ul>
          );
        }

        return (
          <p key={index} className="ltc-article__paragraph">
            {lines.join(" ")}
          </p>
        );
      })}
    </section>
  );
}
