// Renders every dagger in the text as a superscript.
export default function renderDagger(text) {
  if (typeof text !== 'string' || !text.includes('†')) return text;
  return text.split('†').flatMap((part, i, arr) =>
    i < arr.length - 1 ? [part, <sup key={i}>†</sup>] : [part]
  );
}
