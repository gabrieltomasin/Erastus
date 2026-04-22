import Link from "next/link";
import { ThemeToggle } from "./theme-toggle";
import { Dices } from "lucide-react";

export function Header() {
  return (
    <header className="mb-8 flex items-center justify-between border-b border-border pb-4">
      <Link href="/" className="flex items-center gap-2 text-xl font-bold">
        <Dices className="h-6 w-6 text-primary" />
        RPG Session Summary
      </Link>
      <ThemeToggle />
    </header>
  );
}
