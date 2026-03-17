import { FormEvent, ReactNode } from "react";

type InputPanelProps = {
  title: string;
  children: ReactNode;
  submitLabel: string;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

export function InputPanel({ title, children, submitLabel, onSubmit }: InputPanelProps) {
  return (
    <form onSubmit={onSubmit} className="panel grid gap-4 p-6" data-cinematic-reveal="true">
      <h2 className="text-xl font-semibold text-softwhite">{title}</h2>
      {children}
      <button className="holo-btn rounded-lg px-4 py-2 font-hud text-softwhite" type="submit">
        {submitLabel}
      </button>
    </form>
  );
}
