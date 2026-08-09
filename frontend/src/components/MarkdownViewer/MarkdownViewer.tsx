import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./MarkdownViewer.css";

interface Props {
  content: string;
}

export default function MarkdownViewer({ content }: Props) {
  return (
    <div className="md-viewer">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  );
}
