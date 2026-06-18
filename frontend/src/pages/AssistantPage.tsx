import { FormEvent, useState } from "react";
import { Send } from "lucide-react";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { api } from "../services/api";


export function AssistantPage() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<{ role: string; text: string }[]>([
    { role: "assistant", text: "Ask about motion activity, restricted zones, people, vehicles, evidence, or today's summary." }
  ]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!question.trim()) return;
    const text = question.trim();
    setMessages((prev) => [...prev, { role: "user", text }]);
    setQuestion("");
    const { data } = await api.post("/assistant/ask", { question: text });
    setMessages((prev) => [...prev, { role: "assistant", text: data.answer }]);
  }

  return (
    <div className="space-y-6">
      <div><h1 className="text-2xl font-bold text-ink">AI Surveillance Assistant</h1><p className="text-sm text-muted">Answers are generated from your authenticated database records.</p></div>
      <Card>
        <div className="space-y-3">
          {messages.map((message, index) => (
            <div key={index} className={`rounded-2xl p-3 text-sm shadow-sm ${message.role === "user" ? "ml-auto max-w-xl bg-brand text-white" : "max-w-2xl border border-[#E5E7E1] bg-[#F7F8F4] text-muted"}`}>{message.text}</div>
          ))}
        </div>
        <form onSubmit={submit} className="mt-5 flex gap-2">
          <input className="min-h-11 flex-1 rounded-2xl border border-[#E5E7E1] bg-[#F7F8F4] px-3 outline-none transition focus:border-[#5E6B4F] focus:ring-4 focus:ring-[#5E6B4F]/10" value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Which zone has highest risk?" />
          <Button><Send size={16} /> Ask</Button>
        </form>
      </Card>
    </div>
  );
}
