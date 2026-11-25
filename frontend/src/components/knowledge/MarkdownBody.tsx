import Markdown from 'react-markdown';
import remarkBreaks from 'remark-breaks';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github.css';

import { assetUrl } from '../../api/knowledge';

const REMOTE_SRC = /^(https?:|data:|\/)/i;
const HTML_IMG = /<img\b[^>]*?\bsrc=["']([^"']+)["'][^>]*?>/gi;
const ALT_ATTR = /\balt=["']([^"']*)["']/i;

/**
 * Many blogs use <img src="..."> instead of markdown image syntax. Convert those to markdown images so they render
 * through the same image path. Other raw HTML is still not rendered (no rehype-raw), which matches record-app.
 */
export function normalizeHtmlImages(markdown: string): string {
  return markdown.replace(HTML_IMG, (tag: string, src: string) => {
    const alt = tag.match(ALT_ATTR)?.[1] ?? '';
    // Angle brackets allow spaces in the path.
    return `![${alt}](<${src}>)`;
  });
}

/** react-markdown already percent-encodes image URLs; decode once so assetUrl does not encode twice. */
function decodeSrc(src: string): string {
  try {
    return decodeURIComponent(src);
  } catch {
    return src;
  }
}

export function MarkdownBody({ content }: { content: string }) {
  if (!content.trim()) {
    return <p className="text-sm text-muted-foreground">（正文为空）</p>;
  }
  return (
    <div className="prose prose-sm max-w-none dark:prose-invert prose-img:rounded-md">
      <Markdown
        remarkPlugins={[remarkGfm, remarkBreaks]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          img: ({ src, alt }) => {
            const url = !src ? '' : REMOTE_SRC.test(src) ? src : assetUrl(decodeSrc(src));
            return <img src={url} alt={alt ?? ''} loading="lazy" className="mx-auto max-h-[480px]" />;
          },
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noreferrer" className="text-primary underline underline-offset-2">
              {children}
            </a>
          ),
        }}
      >
        {normalizeHtmlImages(content)}
      </Markdown>
    </div>
  );
}
