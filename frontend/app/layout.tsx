import "./styles.css";
import { CopilotKitProvider } from "./copilotkit-provider";

export const metadata = { title: "VibeGraph", description: "Conversational semantic modelling" };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body><CopilotKitProvider>{children}</CopilotKitProvider></body></html>;
}
